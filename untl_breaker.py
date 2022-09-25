"""untl_breaker script for processing OAI-PMH 2.0 Repository XML Files"""

import argparse
import sys
from xml.etree import ElementTree


UNTL_NAMESPACE = "{http://digital2.library.unt.edu/untl/}"
UNTL_NSMAP = {"untl": UNTL_NAMESPACE}

NAME_FIELDS = ["creator", "contributor", "publisher"]


class Record:
    """Base class for a UNTL metadata record in an OAI-PMH
       Repository file."""

    def __init__(self, elem, options):
        self.elem = elem
        self.options = options

    def get_meta_id(self):
        """Returns record ARK identifier."""
        metas = self.elem[1][0].findall(UNTL_NAMESPACE + "meta")
        for meta in metas:
            if meta.get("qualifier") == "ark":
                meta_id = meta.text
                break

        return meta_id

    def get_record_status(self):
        """Returns record status which is either active or deleted"""
        return self.elem.find("header").get("status", "active")

    def get_elements(self):
        """Yields designated element instances from record."""
        elements = self.elem[1][0].findall(UNTL_NAMESPACE + self.options.element)
        for element in elements:
            if element is not None:
                element_dict = {}
                # Name fields have an additional nesting we need to deal with.
                if self.options.element in NAME_FIELDS:
                    name = element.findtext(UNTL_NAMESPACE + "name", "").strip()
                    element_dict["value"] = name
                else:
                    element_dict["value"] = element.text.strip()
                element_dict["value"] = element_dict["value"].replace("\t", " ")
                element_dict["value"] = element_dict["value"].replace("\n", " ")
                element_dict["qualifier"] = element.get("qualifier", 'None')
                # If "value" is empty we want to skip the element.
                if not element_dict["value"]:
                    continue
                # If we have asked for only a specific qualifier, yield only that.
                if self.options.qualifier:
                    if self.options.qualifier == element_dict['qualifier']:
                        yield element_dict
                # We didn't ask for a specific qualifier so yield all of them.
                else:
                    yield element_dict

    def get_all_data(self):
        """Returns a list of all metadata elements and values"""
        for element in self.elem[1][0]:
            text = ''
            if element.tag.replace(UNTL_NAMESPACE, '') in NAME_FIELDS:
                text = element.findtext(UNTL_NAMESPACE + "name", "").strip()
            else:
                text = element.text.strip()
            if text:
                value = text.replace("\t", " ")
                value = value.replace("\n", " ")
                qualifier = element.get("qualifier", None)
                tag = element.tag
                yield (tag, qualifier, value)

    def has_element(self):
        """Returns True or False if a record has value in a selected metadata element"""
        has_elements = self.elem[1][0].findall(UNTL_NAMESPACE + self.options.element)
        for element in has_elements:
            if element.text:
                return True
        return False


def main():
    """Main file handling and option handling"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--element", dest="element", default=None,
                        help="elemnt to print to screen", metavar="subject, creator")
    parser.add_argument("-q", "--qualifier", dest="qualifier", default=None,
                        help="qualifier to limit to", metavar="KWD, officialtitle")
    parser.add_argument("-i", "--id", action="store_true", dest="id", default=False,
                        help="prepend meta_id to line")
    parser.add_argument("-a", "--add-qualifier", action="store_true", dest="add_qualifier",
                        help="prepend qualifier to line",  default=False)
    parser.add_argument("-p", "--present", action="store_true", dest="present", default=False,
                        help="print if there is value of defined element in record")
    parser.add_argument("-d", "--dump", action="store_true", dest="dump", default=False,
                        help="Dump all record data to a tab delimited format")
    parser.add_argument("filename", type=str,
                        help="OAI-PMH UNTL Repository File")

    args = parser.parse_args()

    if (args.element is None and args.dump is False):
        parser.print_help()
        sys.exit(1)

    for _event, elem in ElementTree.iterparse(args.filename):
        if elem.tag == "record":
            record = Record(elem, args)
            meta_id = record.get_meta_id()

            if args.dump is True and record.get_record_status() == "active":
                for field_data in record.get_all_data():
                    print(f"{meta_id}\t{field_data[0]}\t{field_data[1]}\t{field_data[2]}")
                elem.clear()
                continue

            # Present Section
            if args.present is True and record.get_record_status() == "active":
                print(f"{meta_id}\t{record.has_element()}")
                elem.clear()
                continue

            if record.get_elements():
                for i in record.get_elements():
                    if args.id and args.add_qualifier:
                        print(f"{meta_id}\t{i['qualifier']}\t{i['value']}")
                    elif args.add_qualifier:
                        print(f"{i['qualifier']}\t{i['value']}")
                    elif args.id and args.add_qualifier is False:
                        print(f"{meta_id}\t{i['value']}")
                    else:
                        print(i["value"])
            elem.clear()

if __name__ == "__main__":
    main()
