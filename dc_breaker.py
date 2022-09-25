
"""dc_breaker script for processing OAI-PMH 2.0 Repository XML Files"""

import argparse
from xml.etree import ElementTree


OAI_NAMESPACE = "{http://www.openarchives.org/OAI/2.0/oai_dc/}"
DC_NAMESPACE = "{http://purl.org/dc/elements/1.1/}"

METADATA_FIELD_ORDER = ["{http://purl.org/dc/elements/1.1/}title",
                        "{http://purl.org/dc/elements/1.1/}creator",
                        "{http://purl.org/dc/elements/1.1/}contributor",
                        "{http://purl.org/dc/elements/1.1/}publisher",
                        "{http://purl.org/dc/elements/1.1/}date",
                        "{http://purl.org/dc/elements/1.1/}language",
                        "{http://purl.org/dc/elements/1.1/}description",
                        "{http://purl.org/dc/elements/1.1/}subject",
                        "{http://purl.org/dc/elements/1.1/}coverage",
                        "{http://purl.org/dc/elements/1.1/}source",
                        "{http://purl.org/dc/elements/1.1/}relation",
                        "{http://purl.org/dc/elements/1.1/}rights",
                        "{http://purl.org/dc/elements/1.1/}type",
                        "{http://purl.org/dc/elements/1.1/}format",
                        "{http://purl.org/dc/elements/1.1/}identifier"]


class RepoInvestigatorException(Exception):
    """This is our base exception for this script"""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"{self.value}"


class Record:
    """Base class for a Dublin Core metadata record in an OAI-PMH
       Repository file."""

    def __init__(self, elem, options):
        self.elem = elem
        self.options = options

    def get_record_id(self):
        """Returns record identifier or raises error if identifier is not present."""
        try:
            record_id = self.elem.find("header/identifier").text
            return record_id
        except AttributeError as err:
            raise RepoInvestigatorException(
                "Record does not have a valid Record Identifier") from err

    def get_record_status(self):
        """Returns record status which is either active or deleted"""
        return self.elem.find("header").get("status", "active")

    def get_elements(self):
        """Returns a list of values for the selected metadata element"""
        out = []
        elements = self.elem[1][0].findall(DC_NAMESPACE + self.options.element)
        for element in elements:
            if element.text:
                out.append(element.text.strip())
        return out

    def get_all_data(self):
        """Returns a list of all metadata elements and values"""
        out = []
        for i in self.elem[1][0]:
            if i.text:
                out.append((i.tag, i.text.strip().replace("\n", " ")))
        return out

    def get_stats(self):
        """Calculates counts for elements in record"""
        stats = {}
        for element in self.elem[1][0]:
            stats.setdefault(element.tag, 0)
            stats[element.tag] += 1
        return stats

    def has_element(self):
        """Returns True or False if a record has value in a selected metadata element"""
        has_elements = self.elem[1][0].findall(DC_NAMESPACE + self.options.element)
        for element in has_elements:
            if element.text:
                return True
        return False


def collect_stats(stats_aggregate, stats):
    """Collect stats from entire repository"""
    # increment the record counter
    stats_aggregate["record_count"] += 1

    for field in stats:

        # get the total number of times a field occurs
        stats_aggregate["field_info"].setdefault(field, {"field_count": 0})
        stats_aggregate["field_info"][field]["field_count"] += 1

        # get average of all fields
        stats_aggregate["field_info"][field].setdefault("field_count_total", 0)
        stats_aggregate["field_info"][field]["field_count_total"] += stats[field]


def create_stats_averages(stats_aggregate):
    """Create repository averages for stats collected"""
    for field in stats_aggregate["field_info"]:
        field_count = stats_aggregate["field_info"][field]["field_count"]
        field_count_total = stats_aggregate["field_info"][field]["field_count_total"]

        field_count_total_avg = (float(field_count_total) / float(stats_aggregate["record_count"]))
        stats_aggregate["field_info"][field]["field_count_total_average"] = field_count_total_avg

        field_count_elem_avg = (float(field_count_total) / float(field_count))
        stats_aggregate["field_info"][field]["field_count_element_average"] = field_count_elem_avg

    return stats_aggregate


def calc_completeness(stats_averages):
    """Calculate completeness values for repository records"""
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

    for element in sorted(stats_averages["field_info"]):
        elem_comp_perc = 0
        elem_comp_perc = ((stats_averages["field_info"][element]["field_count"] /
                           float(record_count)) * 100)
        completeness_total += elem_comp_perc

        # gather collection completeness
        if elem_comp_perc > 10:
            collection_total += elem_comp_perc
            collection_field_to_count += 1
        # gather wwww completeness
        if element in wwww:
            wwww_total += elem_comp_perc

    completeness["dc_completeness"] = completeness_total / float(15)
    completeness["collection_completeness"] = collection_total / float(collection_field_to_count)
    completeness["wwww_completeness"] = wwww_total / float(len(wwww))
    completeness["average_completeness"] = ((completeness["dc_completeness"] +
                                             completeness["collection_completeness"] +
                                             completeness["wwww_completeness"]) / float(3))
    return completeness


def pretty_print_stats(stats_averages):
    """Generates a pretty table with results"""
    record_count = stats_averages["record_count"]
    # get header length
    element_length = 0
    for element in stats_averages["field_info"]:
        if element_length < len(element):
            element_length = len(element)

    print("\n")
    for element in METADATA_FIELD_ORDER:
        if stats_averages["field_info"].get(element):
            field_count = stats_averages["field_info"][element]["field_count"]
            perc = (field_count / float(record_count)) * 100
            perc_print = "=" * (int(perc) // 4)
            column_one = " " * (element_length - len(element)) + element
            field_count = stats_averages["field_info"][element]["field_count"]
            print(f"{column_one}: |{perc_print:25}| {field_count:6}/{record_count} | {perc:>6.2f}%")

    print("\n")
    completeness = calc_completeness(stats_averages)
    for comp_type in ["dc_completeness",
                      "collection_completeness",
                      "wwww_completeness",
                      "average_completeness"]:
        print(f"{comp_type:>23} {completeness[comp_type]:10.2f}")


def dump_record_values(record_id, record):
    """Iterates through all values in a record and returns a formatted string"""
    if record.get_record_status() == "active":
        record_fields = record.get_all_data()
        for field_data in record_fields:
            field_name = field_data[0]
            field_value = field_data[1].replace("\t", " ")
            yield f"{record_id}\t{field_name}\t{field_value}"


def main():
    """Main file handling and option handling"""
    stats_aggregate = {
        "record_count": 0,
        "field_info": {}
    }

    element_choices = ["title", "creator", "contributor", "publisher", "date", "language",
                       "description", "subject", "coverage", "source", "relation",
                       "rights", "type", "format", "identifier"]
    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--element", dest="element", default=None,
                        help="elemnt to print to screen", choices=element_choices)
    parser.add_argument("-i", "--id", action="store_true", dest="id", default=False,
                        help="prepend meta_id to line")
    parser.add_argument("-s", "--stats", action="store_true", dest="stats", default=False,
                        help="only print stats for repository")
    parser.add_argument("-p", "--present", action="store_true", dest="present", default=False,
                        help="print if there is value of defined element in record")
    parser.add_argument("-d", "--dump", action="store_true", dest="dump", default=False,
                        help="Dump all record data to a tab delimited format")
    parser.add_argument("filename", type=str,
                        help="OAI-PMH Repository File")

    args = parser.parse_args()

    if args.element is None:
        args.stats = True

    record_count = 0
    for _event, elem in ElementTree.iterparse(args.filename):
        if elem.tag == "record":
            record = Record(elem, args)
            record_id = record.get_record_id()

            if args.dump is True:
                # Dumps all values for each record.
                for value in dump_record_values(record_id, record):
                    print(value)
                elem.clear()
                continue  # Skip stats building

            if args.stats is False and args.element and record.get_record_status() == "active":
                for i in record.get_elements():
                    out = [i]
                    if args.id:
                        out.insert(0, record_id)
                    if args.present:
                        out = [record_id, str(record.has_element())]
                    print('\t'.join(out))
                continue  # Skip stats building

            if args.stats is True and record.get_record_status() == "active":
                if (record_count % 1000) == 0 and record_count != 0:
                    print(f"{record_count} records processed")

                collect_stats(stats_aggregate, record.get_stats())
                record_count += 1
            elem.clear()

    if args.stats is True and args.dump is False and args.element is None:
        stats_averages = create_stats_averages(stats_aggregate)
        pretty_print_stats(stats_averages)

if __name__ == "__main__":
    main()
