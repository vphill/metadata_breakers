metadata breakers
=================

Python scripts for "breaking" or atomizing OAI-PMH repositories into simpler text formats. 

These scripts were designed to use the output from [pyoaiharvester](https://github.com/vphill/pyoaiharvester). 

Basic Usage
-----------

Using pyoaiharvester, grab some records you are interested in working with. 

```bash
python3 pyoaiharvest.py -l https://texashistory.unt.edu/explore/collections/ACUC/oai/ -o acuc.dc.xml
```
 
This will result in a repository xml file called `acuc.dc.xml` for the [ACUC collection](https://texashistory.unt.edu/explore/collections/ACUC/) on The Portal to Texas History.

Next you can start to work with the _metadata breakers_. 

```bash
python3 dc_breaker.py ../pyoaiharvester/acuc.dc.xml


      {http://purl.org/dc/elements/1.1/}title: |=========================|    191/191 | 100.00%
    {http://purl.org/dc/elements/1.1/}creator: |=========================|    191/191 | 100.00%
{http://purl.org/dc/elements/1.1/}contributor: |                         |      3/191 |   1.57%
  {http://purl.org/dc/elements/1.1/}publisher: |=========================|    191/191 | 100.00%
       {http://purl.org/dc/elements/1.1/}date: |=========================|    191/191 | 100.00%
   {http://purl.org/dc/elements/1.1/}language: |=========================|    191/191 | 100.00%
{http://purl.org/dc/elements/1.1/}description: |=========================|    191/191 | 100.00%
    {http://purl.org/dc/elements/1.1/}subject: |=========================|    191/191 | 100.00%
   {http://purl.org/dc/elements/1.1/}coverage: |=========================|    191/191 | 100.00%
     {http://purl.org/dc/elements/1.1/}rights: |=                        |     10/191 |   5.24%
       {http://purl.org/dc/elements/1.1/}type: |=========================|    191/191 | 100.00%
     {http://purl.org/dc/elements/1.1/}format: |=========================|    191/191 | 100.00%
 {http://purl.org/dc/elements/1.1/}identifier: |=========================|    191/191 | 100.00%


        dc_completeness      73.79
collection_completeness     100.00
      wwww_completeness     100.00
   average_completeness      91.26
```

You can designate a specific Dublin Core field to list those elements only. 

```bash
python3 dc_breaker.py ../pyoaiharvester/acuc.dc.xml -e title

Catalog of Abilene Christian College, 1906-1907
The Childers Classical Institute, Abilene, Texas, Catalog 1906-1907
Announcements 1907-1908
Catalog of Abilene Christian College, 1910-1911
Fifth Annual Catalogue, Abilene Christian College, Abilene, Texas, 1910-1911
Announcement 1910-1911
Catalog of Abilene Christian College, 1912-1913
Seventh Annual Announcement, Abilene Christian College, Abilene, Texas, 1912-1913
Announcement 1912-1913
Catalog of Abilene Christian College, 1913-1914
```

You can prepend the identifier for the record to the line with the `-i` flag. 

```bash

python3 dc_breaker.py ../pyoaiharvester/acuc.dc.xml -e title -i | head
info:ark/67531/metapth45902	Catalog of Abilene Christian College, 1906-1907
info:ark/67531/metapth45902	The Childers Classical Institute, Abilene, Texas, Catalog 1906-1907
info:ark/67531/metapth45902	Announcements 1907-1908
info:ark/67531/metapth45910	Catalog of Abilene Christian College, 1910-1911
info:ark/67531/metapth45910	Fifth Annual Catalogue, Abilene Christian College, Abilene, Texas, 1910-1911
info:ark/67531/metapth45910	Announcement 1910-1911
info:ark/67531/metapth45909	Catalog of Abilene Christian College, 1912-1913
info:ark/67531/metapth45909	Seventh Annual Announcement, Abilene Christian College, Abilene, Texas, 1912-1913
info:ark/67531/metapth45909	Announcement 1912-1913
info:ark/67531/metapth45908	Catalog of Abilene Christian College, 1913-1914
```

More examples and a full explination of how you might use this tool as part of metadata analysis can be found in the article [Metadata Analysis at the Command-Line](https://journal.code4lib.org/articles/7818)
