import sys
from optparse import OptionParser
from xml.etree import ElementTree

class RepoInvestigatorException(Exception):
    """This is our base exception for this script"""
    def __init__(self, value):
        self.value = value
   
    def __str__(self):
        return "%s" % (self.value,)

UNTL_NAMESPACE = "{http://digital2.library.unt.edu/untl/}"
UNTL = "{%s}" % UNTL_NAMESPACE
UNTL_NSMAP = { "untl" : UNTL_NAMESPACE }

name_fields = ["creator", "contributor", "publisher"]
    
class Record:
    
    def __init__(self, elem, options):
        self.elem = elem
        self.options = options
        
        
    def get_meta_id(self):
        metas = self.elem[1][0].findall(UNTL_NAMESPACE + "meta")
        for meta in metas:
            if meta.get("qualifier") == "ark":
                self.meta_id = meta.text
                break
            else:
                self.meta_id = None
        return self.meta_id
        
        
    def get_record_status(self):
        return self.elem.find("header").get("status", "active")
        
        
    def get_elements(self):
        out = []
        elements = self.elem[1][0].findall(UNTL_NAMESPACE + self.options.element)
        if self.options.element in name_fields:
            for element in elements:
                if self.options.qualifier:
                    if element.get("qualifier", None) == self.options.qualifier:
                        print("t")
                        try:
                            element_dict = {}
                            element_dict["value"] = element.find(UNTL_NAMESPACE + "name").text.encode("utf-8").strip()
                            element_dict["qualifier"] = element.get("qualifier", None)
                            out.append(element_dict)
                        except:
                            pass
                else:
                    try:
                        element_dict = {}
                        element_dict["value"] = element.find(UNTL_NAMESPACE + "name").text.encode("utf-8").strip()
                        element_dict["qualifier"] = element.get("qualifier", None)
                        out.append(element_dict)
                    except:
                        pass
        else:
            for element in elements:
                if self.options.qualifier:
                    if element.get("qualifier", None) == self.options.qualifier:
                        element_dict = {}
                        element_dict["value"] = element.text.encode("utf-8").strip()
                        element_dict["qualifier"] = element.get("qualifier", None)
                        out.append(element_dict)
                else:
                    element_dict = {}
                    element_dict["value"] = element.text.encode("utf-8").strip()
                    element_dict["qualifier"] = element.get("qualifier", None)
                    out.append(element_dict)
                    
        if len(out) == 0:
            out = None
        return out
        
        
    def get_all_data(self):
        out = []
        for i in self.elem[1][0]:
            if i.tag.rsplit("}")[-1] in name_fields:
                try:
                    text = i.find(UNTL_NAMESPACE + "name").strip()
                except:
                    text = "None"
            else:
                text = i.text.strip()
            value = text.replace("\t", " ")
            value = value.replace("\n", " ")
            qualifier = i.get("qualifier", None)
            tag = i.tag
            out.append((tag, qualifier, value))
        return out


def main():
    usage = "usage: %prog [options] <OAI-PMH Repository File"
    parser = OptionParser(usage)
    parser.add_option("-e", "--element", dest="element",
                  help="elemnt to print to screen", metavar="subject, creator")
    parser.add_option("-q", "--qualifier", dest="qualifier",
                  help="qualifier to limit to", metavar="KWD, officialtitle")
    parser.add_option("-i", "--id", action="store_true", dest="id", default=False,
                  help="prepend meta_id to line")
    parser.add_option("-a", "--add-qualifier", action="store_true", dest="add_qualifier", default=False,
                  help="prepend meta_id to line")
    parser.add_option("-p", "--present", action="store_true", dest="present", default=False,
                  help="print if there is value of defined element in record")
    parser.add_option("-d", "--dump", action="store_true", dest="dump", default=False,
                  help="Dump all record data to a tab delimited format")
    
    
    (options, args) = parser.parse_args()
    
    if len(args) == 0:
        print(usage)
        exit()
    
    for event, elem in ElementTree.iterparse(args[0]):
        if elem.tag == "record":
            r = Record(elem, options)
            meta_id = r.get_meta_id()
            
            if options.dump == True:
                if r.get_record_status() != "deleted":
                    record_fields = r.get_all_data()
                    for field_data in record_fields:
                        print("{}\t{}\t{}\t{}".format(meta_id, field_data[0], field_data[1], field_data[2]))
                elem.clear()
                continue

            # Present Section
            if options.present == True:
                if r.get_record_status() != "deleted":
                    if r.get_elements() == None:
                        present = False
                    else:
                        present = True
                    print("{}\t{}".format(meta_id, present))
                elem.clear()
                continue
                
            if r.get_elements() != None :
                for i in r.get_elements():
                        if options.id and options.add_qualifier:
                            print("{}\t{}\t{}".format((meta_id, i["qualifier"], i["value"].decode('utf-8'))))
                        elif options.add_qualifier:
                            print("{}\t{}".format((i["qualifier"], i["value"].decode('utf-8'))))
                        elif options.id and options.add_qualifier == False:
                            print("{}\t{}".format(meta_id, i["value"].decode('utf-8').replace('\n', ' ').replace('\t', ' ')))
                        else:
                            print(i["value"].decode('utf-8'))
            elem.clear()
if __name__ == "__main__":
    main()
    
