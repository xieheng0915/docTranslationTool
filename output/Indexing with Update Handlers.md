



# Indexing with Update Handlers



Update handlers are request handlers designed to add, delete and update documents to the index.
In addition to having plugins for importing rich documents (see Indexing with Solr Cell and Apache Tika), Solr natively supports indexing structured documents in XML, CSV, and JSON.



The recommended way to configure and use request handlers is with path based names that map to paths in the request URL.
However, request handlers can also be specified with the qt (query type) parameter if the requestDispatcher is appropriately configured.
It is possible to access the same handler using more than one name, which can be useful if you wish to specify different sets of default options.



A single unified update request handler supports XML, CSV, JSON, and javabin update requests, delegating to the appropriate ContentStreamLoader based on the Content-Type of the ContentStream.



If you need to pre-process documents after they are loaded but before they are indexed (or even checked against the schema),
Solr has document preprocessing plugins for Update Request Handlers, called Update Request Processors, which allow for default and custom configuration chains.

## UpdateRequestHandler Configuration


The default configuration file has the update request handler configured by default.
```
<requestHandler name="/update" class="solr.UpdateRequestHandler" />
```

## XML Formatted Index Updates


Index update commands can be sent as XML message to the update handler using Content-type: application/xml or Content-type: text/xml.
### Adding Documents


The XML schema recognized by the update handler for adding documents is very straightforward:
- The <add> element introduces one more documents to be added.
- The <doc> element introduces the fields making up a document.
- The <field> element presents the content for a specific field.


For example:
```
<add>
  <doc>
    <field name="authors">Patrick Eagar</field>
    <field name="subject">Sports</field>
    <field name="dd">796.35</field>
    <field name="numpages">128</field>
    <field name="desc"></field>
    <field name="price">12.40</field>
    <field name="title">Summer of the all-rounder: Test and championship cricket in England 1982</field>
    <field name="isbn">0002166313</field>
    <field name="yearpub">1982</field>
    <field name="publisher">Collins</field>
  </doc>
  <doc>
  ...
  </doc>
</add>
```


The add command supports some optional attributes which may be specified.  
**commitWithin**
|Optional|Default: none|
| :---: | :---: |
  
*Add the document within the specified number of milliseconds.*  
**overwrite**
|Optional|Default: true|
| :---: | :---: |
  
*Indicates if the unique key constraints should be checked to overwrite previous versions of the same document (see below).*

If the document schema defines a unique key, then by default an /update operation to add a document will overwrite (i.e., replace) any document in the index with the same unique key.
If no unique key has been defined, indexing performance is somewhat faster, as no check has to be made for an existing documents to replace.

If you have a unique key field, but you feel confident that you can safely bypass the uniqueness check (e.g., you build your indexes in batch, and your indexing code guarantees it never adds the same document more than once) you can specify the overwrite="false" option when adding your documents.
### XML Update Commands

#### Commit and Optimize During Updates


The <commit> operation writes all documents loaded since the last commit to one or more segment files on the disk.
Before a commit has been issued, newly indexed content is not visible to searches.
The commit operation opens a new searcher, and triggers any event listeners that have been configured.

Commits may be issued explicitly with a <commit/> message, and can also be triggered from <autocommit> parameters in solrconfig.xml.

The <optimize> operation requests Solr to merge internal data structures.
For a large index, optimization will take some time to complete, but by merging many small segment files into larger segments, search performance may improve.
If you are using Solr’s replication mechanism to distribute searches across many systems, be aware that after an optimize, a complete index will need to be transferred.  
:warning:Warning  

You should only consider using optimize on static indexes, i.e., indexes that can be optimized as part of the regular update process (say once-a-day updates).
Applications requiring NRT functionality should not use optimize.


The <commit> and <optimize> elements accept these optional attributes:  
**waitSearcher**
|Optional|Default: true|
| :---: | :---: |
  
*Blocks until a new searcher is opened and registered as the main query searcher, making the changes visible.*  
**expungeDeletes**
|Optional|Default: false|
| :---: | :---: |
  
*Merges segments that have more than 10% deleted docs, expunging the deleted documents in the process.Resulting segments will respect maxMergedSegmentMB.This option only applies in a <commit> operation.*  
**maxSegments**
|Optional|Default: none|
| :---: | :---: |
  
*Makes a best effort attempt to merge the segments down to no more than this number of segments but does not guarantee that the goal will be achieved.Unless there is tangible evidence that optimizing to a small number of segments is beneficial, this parameter should be omitted and the default behavior accepted.This option only applies in a <optimize operation.Default is unlimited, resulting segments respect the maxMergedSegmentMB setting.*

Here are examples of <commit> and <optimize> using optional attributes:
```
<commit waitSearcher="false"/>
<commit waitSearcher="false" expungeDeletes="true"/>
<optimize waitSearcher="false"/>
```

#### Delete Operations


Documents can be deleted from the index in two ways.
"Delete by ID" deletes the document with the specified ID, and can be used only if a UniqueID field has been defined in the schema.
It doesn’t work for child/nested docs.
"Delete by Query" deletes all documents matching a specified query, although commitWithin is ignored for a Delete by Query.
A single delete message can contain multiple delete operations.
```
<delete>
  <id>0002166313</id>
  <id>0031745983</id>
  <query>subject:sport</query>
  <query>publisher:penguin</query>
</delete>
```
  
:exclamation:Important  


When using the Join query parser in a Delete By Query, you should use the score parameter with a value of "none" to avoid a ClassCastException.
See the section on the Join Query Parser for more details on the score parameter.


#### Rollback Operations


The rollback command rolls back all add and deletes made to the index since the last commit.
It neither calls any event listeners nor creates a new searcher.
Its syntax is simple: <rollback/>.
#### Grouping Operations


You can post several commands in a single XML file by grouping them with the surrounding <update> element.
```
<update>
  <add>
    <doc><!-- doc 1 content --></doc>
  </add>
  <add>
    <doc><!-- doc 2 content --></doc>
  </add>
  <delete>
    <id>0002166313</id>
  </delete>
</update>
```

### Using curl to Perform Updates


You can use the curl utility to perform any of the above commands, using its --data-binary option to append the XML message to the curl command, and generating a HTTP POST request.
For example:
```
curl http://localhost:8983/solr/my_collection/update -H "Content-Type: text/xml" --data-binary '
<add>
  <doc>
    <field name="authors">Patrick Eagar</field>
    <field name="subject">Sports</field>
    <field name="dd">796.35</field>
    <field name="isbn">0002166313</field>
    <field name="yearpub">1982</field>
    <field name="publisher">Collins</field>
  </doc>
</add>'
```


For posting XML messages contained in a file, you can use the alternative form:
```
curl http://localhost:8983/solr/my_collection/update -H "Content-Type: text/xml" --data-binary @myfile.xml
```


The approach above works well, but using the --data-binary option causes curl to load the whole myfile.xml into memory before posting it to server.
This may be problematic when dealing with multi-gigabyte files.
This alternative curl command performs equivalent operations but with minimal curl memory usage:
```
curl http://localhost:8983/solr/my_collection/update -H "Content-Type: text/xml" -T "myfile.xml" -X POST
```


Short requests can also be sent using a HTTP GET command, if enabled in requestParsers element of solrconfig.xml, URL-encoding the request, as in the following.
Note the escaping of "<" and ">":
```
curl http://localhost:8983/solr/my_collection/update?stream.body=%3Ccommit/%3E&wt=xml
```


Responses from Solr take the form shown here:
```
<response>
  <lst name="responseHeader">
    <int name="status">0</int>
    <int name="QTime">127</int>
  </lst>
</response>
```


The status field will be non-zero in case of failure.
### Using XSLT to Transform XML Index Updates


The Scripting module provides a separate XSLT Update Request Handler that allows you to index any arbitrary XML by using the <tr> parameter to apply an XSL transformation.
You must have an XSLT stylesheet in the conf/xslt directory of your configset that can transform the incoming data to the expected <add><doc/></add> format, and use the tr parameter to specify the name of that stylesheet.

You will need to enable the scripting Module before using this feature.
### tr Parameter


The XSLT Update Request Handler accepts the tr parameter, which identifies the XML transformation to use.
The transformation must be found in the Solr conf/xslt directory.
### XSLT Configuration


The example below, from the sample_techproducts_configs configset in the Solr distribution, shows how the XSLT Update Request Handler is configured.
```
<!--
  Changes to XSLT transforms are taken into account
  every xsltCacheLifetimeSeconds at most.
-->
<requestHandler name="/update/xslt"
                     class="solr.scripting.xslt.XSLTUpdateRequestHandler">
  <int name="xsltCacheLifetimeSeconds">5</int>
</requestHandler>
```


A value of 5 for xsltCacheLifetimeSeconds is good for development, to see XSLT changes quickly.
For production you probably want a much higher value.
### XSLT Update Example


Here is the sample_techproducts_configs/conf/xslt/updateXml.xsl XSL file for converting standard Solr XML output to the Solr expected <add><doc/></add> format:
```
<xsl:stylesheet version='1.0' xmlns:xsl='http://www.w3.org/1999/XSL/Transform'>
  <xsl:output media-type="text/xml" method="xml" indent="yes"/>
  <xsl:template match='/'>
    <add>
      <xsl:apply-templates select="response/result/doc"/>
    </add>
  </xsl:template>
  <!-- Ignore score (makes no sense to index) -->
  <xsl:template match="doc/*[@name='score']" priority="100"></xsl:template>
  <xsl:template match="doc">
    <xsl:variable name="pos" select="position()"/>
    <doc>
      <xsl:apply-templates>
        <xsl:with-param name="pos"><xsl:value-of select="$pos"/></xsl:with-param>
      </xsl:apply-templates>
    </doc>
  </xsl:template>
  <!-- Flatten arrays to duplicate field lines -->
  <xsl:template match="doc/arr" priority="100">
    <xsl:variable name="fn" select="@name"/>
    <xsl:for-each select="*">
      <xsl:element name="field">
        <xsl:attribute name="name"><xsl:value-of select="$fn"/></xsl:attribute>
        <xsl:value-of select="."/>
      </xsl:element>
    </xsl:for-each>
  </xsl:template>
  <xsl:template match="doc/*">
    <xsl:variable name="fn" select="@name"/>
      <xsl:element name="field">
        <xsl:attribute name="name"><xsl:value-of select="$fn"/></xsl:attribute>
      <xsl:value-of select="."/>
    </xsl:element>
  </xsl:template>
  <xsl:template match="*"/>
</xsl:stylesheet>
```


This stylesheet transforms Solr’s XML search result format into Solr’s Update XML syntax.
One example usage would be to copy a Solr 1.3 index (which does not have CSV response writer) into a format which can be indexed into another Solr file (provided that all fields are stored):
```
$ curl -o standard_solr_xml_format.xml "http://localhost:8983/solr/techproducts/select?q=ipod&fl=id,cat,name,popularity,price,score&wt=xml"

$ curl -X POST -H "Content-Type: text/xml" -d @standard_solr_xml_format.xml "http://localhost:8983/solr/techproducts/update/xslt?commit=true&tr=updateXml.xsl"
```
  
:information_source:Note  

You can see the opposite export/import cycle using the tr parameter in the Response Writer XSLT example.

## JSON Formatted Index Updates


Solr can accept JSON that conforms to a defined structure, or can accept arbitrary JSON-formatted documents.
If sending arbitrarily formatted JSON, there are some additional parameters that need to be sent with the update request, described in the section Transforming and Indexing Custom JSON.
### Solr-Style JSON


JSON formatted update requests may be sent to Solr’s /update handler using Content-Type: application/json or Content-Type: text/json.

JSON formatted updates can take 3 basic forms, described in depth below:
- A single document, expressed as a top level JSON Object.
To differentiate this from a set of commands, the json.command=false request parameter is required.
- A list of documents, expressed as a top level JSON Array containing a JSON Object per document.
- A sequence of update commands, expressed as a top level JSON Object (a Map).

#### Adding a Single JSON Document


The simplest way to add documents via JSON is to send each document individually as a JSON Object, using the /update/json/docs path:
```
curl -X POST -H 'Content-Type: application/json' 'http://localhost:8983/solr/my_collection/update/json/docs' --data-binary '
{
  "id": "1",
  "title": "Doc 1"
}'
```

#### Adding Multiple JSON Documents


Adding multiple documents at one time via JSON can be done via a JSON Array of JSON Objects, where each object represents a document:
```
curl -X POST -H 'Content-Type: application/json' 'http://localhost:8983/solr/my_collection/update' --data-binary '
[
  {
    "id": "1",
    "title": "Doc 1"
  },
  {
    "id": "2",
    "title": "Doc 2"
  }
]'
```


A sample JSON file is provided at example/exampledocs/books.json and contains an array of objects that you can add to the Solr "techproducts" example:
```
curl 'http://localhost:8983/solr/techproducts/update?commit=true' --data-binary @example/exampledocs/books.json -H 'Content-type:application/json'
```

#### Sending JSON Update Commands


In general, the JSON update syntax supports all of the update commands that the XML update handler supports, through a straightforward mapping.
Multiple commands, adding and deleting documents, may be contained in one message:
```
curl -X POST -H 'Content-Type: application/json' 'http://localhost:8983/solr/my_collection/update' --data-binary '
{
  "add": {
    "doc": {
      "id": "DOC1",
      "my_field": 2.3,
      "my_multivalued_field": [ "aaa", "bbb" ]   (1)
    }
  },
  "add": {
    "commitWithin": 5000, (2)
    "overwrite": false,  (3)
    "doc": {
      "f1": "v1", (4)
      "f1": "v2"
    }
  },

  "commit": {},
  "optimize": { "waitSearcher":false },

  "delete": { "id":"ID" },  (5)
  "delete": { "query":"QUERY" } (6)
}'
```


As with other update handlers, parameters such as commit, commitWithin, optimize, and overwrite may be specified in the URL instead of in the body of the message.

The JSON update format allows for a simple delete-by-id.
The value of a delete can be an array which contains a list of zero or more specific document id’s (not a range) to be deleted.
For example, a single document:
```
{ "delete":"myid" }
```


Or a list of document IDs:
```
{ "delete":["id1","id2"] }
```


Note: Delete-by-id doesn’t work for child/nested docs.

You can also specify _version_ with each "delete":
```
{
  "delete":"id":50,
  "_version_":12345
}
```


You can specify the version of deletes in the body of the update request as well.
### JSON Update Convenience Paths


In addition to the /update handler, there are a few additional JSON specific request handler paths available by default in Solr, that implicitly override the behavior of some request parameters:

The /update/json path may be useful for clients sending in JSON formatted update commands from applications where setting the Content-Type proves difficult, while the /update/json/docs path can be particularly convenient for clients that always want to send in documents â either individually or as a list â without needing to worry about the full JSON command syntax.
### Custom JSON Documents


Solr can support custom JSON.
This is covered in the section Transforming and Indexing Custom JSON.
## CSV Formatted Index Updates


CSV formatted update requests may be sent to Solr’s /update handler using Content-Type: application/csv or Content-Type: text/csv.

A sample CSV file is provided at example/exampledocs/books.csv that you can use to add some documents to the Solr "techproducts" example:
```
curl 'http://localhost:8983/solr/my_collection/update?commit=true' --data-binary @example/exampledocs/books.csv -H 'Content-type:application/csv'
```

### CSV Update Parameters


The CSV handler allows the specification of many parameters in the URL in the form: f.parameter.optional_fieldname=value.

The table below describes the parameters for the update handler.  
**separator**
|Optional|Default: ,|
| :---: | :---: |
  
*Character used as field separator.This parameter is global; for per-field usage, see the split parameter.*  
**trim**
|Optional|Default: false|
| :---: | :---: |
  
*If true, remove leading and trailing whitespace from values.This parameter can be either global or per-field.*  
**header**
|Optional|Default: true|
| :---: | :---: |
  
*Set to true if first line of input contains field names.These will be used if the fieldnames parameter is absent.This parameter is global.*  
**fieldnames**
|Optional|Default: none|
| :---: | :---: |
  
*Comma-separated list of field names to use when adding documents.This parameter is global.*  
**literal.field_name**
|Optional|Default: none|
| :---: | :---: |
  
*A literal value for a specified field name.This parameter is global.*  
**skip**
|Optional|Default: none|
| :---: | :---: |
  
*Comma separated list of field names to skip.This parameter is global.*  
**skipLines**
|Optional|Default: 0|
| :---: | :---: |
  
*Number of lines to discard in the input stream before the CSV data starts, including the header, if present.This parameter is global.*  
**encapsulator**
|Optional|Default: none|
| :---: | :---: |
  
*The character optionally used to surround values to preserve characters such as the CSV separator or whitespace.This standard CSV format handles the encapsulator itself appearing in an encapsulated value by doubling the encapsulator.*  
**escape**
|Optional|Default: none|
| :---: | :---: |
  
*The character used for escaping CSV separators or other reserved character.If an escape is specified, the encapsulator is not used unless also explicitly specified since most formats use either encapsulation or escaping, not both.*  
**keepEmpty**
|Optional|Default: false|
| :---: | :---: |
  
*Keep and index zero length (empty) fields.This parameter can be global or per-field.*  
**map**
|Optional|Default: none|
| :---: | :---: |
  
*Map one value to another.Format is map=value:replacement (which can be empty).This parameter can be global or per-field.*  
**split**
|Optional|Default: none|
| :---: | :---: |
  
*If true, split a field into multiple values by a separate parser.This parameter is used on a per-field basis, for example f.FIELD_NAME_GOES_HERE.split=true.*  
**overwrite**
|Optional|Default: true|
| :---: | :---: |
  
*If true, check for and overwrite duplicate documents, based on the uniqueKey field declared in the Solr schema.If you know the documents you are indexing do not contain any duplicates then you may see a considerable speed up setting this to false.*  
**commit**
|Optional|Default: none|
| :---: | :---: |
  
*Issues a commit after the data has been ingested.This parameter is global.*  
**commitWithin**
|Optional|Default: none|
| :---: | :---: |
  
*Add the document within the specified number of milliseconds.This parameter is global.*  
**rowid**
|Optional|Default: none|
| :---: | :---: |
  
*Map the rowid (line number) to a field specified by the value of the parameter, for instance if your CSV doesn’t have a unique key and you want to use the row id as such.This parameter is global.*  
**rowidOffset**
|Optional|Default: 0|
| :---: | :---: |
  
*Add the given offset (as an integer) to the rowid before adding it to the document.This parameter is global.*
### Indexing Tab-Delimited files


The same feature used to index CSV documents can also be easily used to index tab-delimited files (TSV files) and even handle backslash escaping rather than CSV encapsulation.

For example, one can dump a MySQL table to a tab-delimited file with:
```
SELECT * INTO OUTFILE '/tmp/result.txt' FROM mytable;
```


This file could then be imported into Solr by setting the separator to tab (%09) and the escape to backslash (%5c).
```
curl 'http://localhost:8983/solr/my_collection/update/csv?commit=true&separator=%09&escape=%5c' --data-binary @/tmp/result.txt
```

### CSV Update Convenience Paths


In addition to the /update handler, there is an additional CSV specific request handler path available by default in Solr, that implicitly override the behavior of some request parameters:

The /update/csv path may be useful for clients sending in CSV formatted update commands from applications where setting the Content-Type proves difficult.