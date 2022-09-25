import hashlib
import sys
import pprint
from optparse import OptionParser
from xml.etree import ElementTree


class RepoInvestigatorException(Exception):
    """This is our base exception for this script"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return "%s" % (self.value,)

OAI_NAMESPACE = "{http://www.openarchives.org/OAI/2.0/oai_dc/}"
DC_NAMESPACE = "{http://purl.org/dc/elements/1.1/}"


class Record:
    """Base class for a Dublin Core metadata record in an OAI-PMH
       Repository file."""

    def __init__(self, elem, options):
        self.elem = elem
        self.options = options

    def get_record_id(self):
        try:
            record_id = self.elem.find("header/identifier").text
            return record_id
        except:
            raise RepoInvestigatorException("Record does not have a valid Record Identifier")

    def get_record_status(self):
        return self.elem.find("header").get("status", "active")

    def get_elements(self):
        out = []
        elements = self.elem[1][0].findall(DC_NAMESPACE + self.options.element)
        for element in elements:
            if element.text:
                out.append(element.text.encode("utf-8").strip())
        if len(out) == 0:
            out = None
        self.elements = out
        return self.elements

    def get_all_data(self):
        out = []
        for i in self.elem[1][0]:
            if i.text:
                out.append((i.tag, i.text.encode("utf-8").strip().replace("\n", " ")))
        return out

    def get_stats(self):
        stats = {}
        for element in self.elem[1][0]:
            stats.setdefault(element.tag, 0)
            stats[element.tag] += 1
        return stats

    def has_element(self):
        out = []
        elements = self.elem[1][0].findall(DC_NAMESPACE + self.options.element)
        for element in elements:
            if element.text:
                return True
        return False


def collect_stats(stats_aggregate, stats):
    #increment the record counter
    stats_aggregate["record_count"] += 1

    for field in stats:

        # get the total number of times a field occurs
        stats_aggregate["field_info"].setdefault(field, {"field_count": 0})
        stats_aggregate["field_info"][field]["field_count"] += 1

        # get average of all fields
        stats_aggregate["field_info"][field].setdefault("field_count_total", 0)
        stats_aggregate["field_info"][field]["field_count_total"] += stats[field]


def create_stats_averages(stats_aggregate):
    for field in stats_aggregate["field_info"]:
        field_count = stats_aggregate["field_info"][field]["field_count"]
        field_count_total = stats_aggregate["field_info"][field]["field_count_total"]

        field_count_total_average = (float(field_count_total) / float(stats_aggregate["record_count"]))
        stats_aggregate["field_info"][field]["field_count_total_average"] = field_count_total_average

        field_count_element_average = (float(field_count_total) / float(field_count))
        stats_aggregate["field_info"][field]["field_count_element_average"] = field_count_element_average

    return stats_aggregate


def calc_completeness(stats_averages):
    completeness = {}
    record_count = stats_averages["record_count"]
    completeness_total = 0
    wwww_total = 0
    collection_total = 0
    collection_field_to_count = 0

    wwww = [
        "{http://purl.org/dc/elements/1.1/}creator",       # who
        "{http://purl.org/dc/elements/1.1/}title",         # what
        "{http://purl.org/dc/elements/1.1/}identifier",    # where
        "{http://purl.org/dc/elements/1.1/}date"           # when
    ]

    populated_elements = len(stats_averages["field_info"])
    for element in sorted(stats_averages["field_info"]):
            element_completeness_percent = 0
            element_completeness_percent = ((stats_averages["field_info"][element]["field_count"]
                                             / float(record_count)) * 100)
            completeness_total += element_completeness_percent

            #gather collection completeness
            if element_completeness_percent > 10:
                collection_total += element_completeness_percent
                collection_field_to_count += 1
            #gather wwww completeness
            if element in wwww:
                wwww_total += element_completeness_percent

    completeness["dc_completeness"] = completeness_total / float(15)
    completeness["collection_completeness"] = collection_total / float(collection_field_to_count)
    completeness["wwww_completeness"] = wwww_total / float(len(wwww))
    completeness["average_completeness"] = ((completeness["dc_completeness"] +
                                             completeness["collection_completeness"] +
                                             completeness["wwww_completeness"]) / float(3))
    return completeness


def pretty_print_stats(stats_averages):
    record_count = stats_averages["record_count"]
    #get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print("\n\n")
    for element in sorted(stats_averages["field_info"]):
        percent = (stats_averages["field_info"][element]["field_count"] / float(record_count)) * 100
        percentPrint = "=" * (int(percent) // 4)
        columnOne = " " * (element_length - len(element)) + element
        print("%s: |%-25s| %6s/%s | %3d%% " % (
            columnOne,
            percentPrint,
            stats_averages["field_info"][element]["field_count"],
            record_count,
            percent
        ))

    print("\n")
    completeness = calc_completeness(stats_averages)
    for i in ["dc_completeness", "collection_completeness", "wwww_completeness", "average_completeness"]:
        print("%23s %f" % (i, completeness[i]))


def main():
    usage = "usage: %prog [options] <OAI-PMH Repository File"
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }
    element_stats_aggregate = {}

    parser = OptionParser(usage)
    parser.add_option("-e", "--element", dest="element",
                      help="elemnt to print to screen")
    parser.add_option("-i", "--id", action="store_true", dest="id", default=False,
                      help="prepend meta_id to line")
    parser.add_option("-s", "--stats", action="store_true", dest="stats", default=False,
                      help="only print stats for repository")
    parser.add_option("-p", "--present", action="store_true", dest="present", default=False,
                      help="print if there is value of defined element in record")
    parser.add_option("-d", "--dump", action="store_true", dest="dump", default=False,
                      help="Dump all record data to a tab delimited format")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        print(usage)
        exit()

    if options.element is None:
        options.stats = True

    s = 0
    for event, elem in ElementTree.iterparse(args[0]):
        if elem.tag == "record":
            r = Record(elem, options)
            record_id = r.get_record_id()

            if options.dump is True:
                if r.get_record_status() != "deleted":
                    record_fields = r.get_all_data()
                    for field_data in record_fields:
                        print("%s\t%s\t%s" % (record_id, field_data[0], field_data[1].replace("\t", " ")))
                elem.clear()
                continue

            if options.stats is False and options.present is False:
                #move along if record is deleted
                if r.get_record_status() != "deleted" and r.get_elements() is not None:
                    for i in r.get_elements():
                        if options.id:
                            print("\t".join([record_id, i]))
                        else:
                            print(i)

            if options.stats is False and options.present is True:
                if r.get_record_status() != "deleted":
                    print("%s %s" % (record_id, r.has_element()))

            if options.stats is True and options.element is None:
                if (s % 1000) == 0 and s != 0:
                    print("%d records processed" % s)
                s += 1
                if r.get_record_status() != "deleted":
                    collect_stats(stats_aggregate, r.get_stats())
            elem.clear()

    if options.stats is True and options.element is None and options.dump is False:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
