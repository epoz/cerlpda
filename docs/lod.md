# Linked Open Data

The CERL Thesaurus [is available as Linked Data](https://www.cerl.org/resources/cerl_thesaurus/linkeddata)
We would like to also model the PDA as Linked Data, and model it to match and link to the CERL Thesaurus and other Linked Data sources [like the STCN](http://data.bibliotheken.nl/doc/nbt/p192741446) or [The RBMS Controlled Vocabulary for Rare Materials Cataloging](https://id.loc.gov/vocabulary/rbmscv.html)

In time, we would like to offer all the CERL PDA data queryable under a SPARQL endpoint, and downloadable as raw RDF data dumps.
This page serves as work-in-progress documentation, as we work towards that goal. We welcome all comments and suggestions, please contact us at secretariat@cerl.org or you can contact [the software maintainers](https://epoz.org/).

## Field Lists

As a start, here is a list of the current choices that can be made for the various fields. These should in due course be given properties that map to the relevant standard vocabularies.

### Type of Provenance Mark

| Entry                               | IRI |
| ----------------------------------- | --- |
| Unknown                             |     |
| Binding                             |     |
| Bookseller’s label                  |     |
| Coat of arms                        |     |
| (De)accession mark                  |     |
| Decoration                          |     |
| Ex-Libris                           |     |
| Manuscript annotations / marginalia |     |
| Monogram                            |     |
| Motto                               |     |
| Old shelfmark                       |     |
| Ownership inscription               |     |
| Purchase information / prices       |     |
| Stamp                               |     |
| Supralibros                         |     |

### Location in Source

| Entry             | IRI |
| ----------------- | --- |
| Title page        |     |
| Front cover       |     |
| Back cover        |     |
| Front pastedown   |     |
| Back pastedown    |     |
| Front endleaves   |     |
| Back endleaves    |     |
| Spine             |     |
| Upper edge        |     |
| Lower edge        |     |
| Fore-edge         |     |
| Page/Folio number |     |

### Technique

| Entry        | IRI |
| ------------ | --- |
| Blind Stamp  |     |
| Drawings     |     |
| Firestamp    |     |
| Gold         |     |
| Illumination |     |
| Ink          |     |
| Pencil       |     |
| Printed      |     |
| Silver       |     |
| Stamp        |     |
| other        |     |
| Unidentified |     |

## TODO

- _Data Cleaning_ Due to historical data entry to the CERL PDA, there are fields in the current dataset that do not exactly map to the choices shown above. As part of the RDF dump process, we need to identify these entries and do a reconcilation.

- _Add links_ to item view page that show RDF data (turtle/json-ld)

- Make _data dump_ for entire PDA in .ttl format

- Add a _/sparql_ endpoint

- Make some user-friendly SPARQL data _query examples_

- Investigate _alternative query user interfaces_
