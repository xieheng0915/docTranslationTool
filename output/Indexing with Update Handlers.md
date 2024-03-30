



# アップデートハンドラーを使用したインデックス作成


更新ハンドラーは、インデックスにドキュメントを追加、削除、更新するために設計されたリクエストハンドラーです。
Solrには、リッチドキュメントをインポートするためのプラグイン（Solr CellおよびApache Tikaを参照）だけでなく、XML、CSV、JSONの構造化されたドキュメントをインデックスするネイティブサポートもあります。

リクエストハンドラーを設定し使用する推奨方法は、リクエストURLのパスにマップされるパスベースの名前を使用することです。
ただし、リクエストディスパッチャーが適切に設定されている場合は、qt（クエリタイプ）パラメーターでリクエストハンドラーを指定することもできます。
同じハンドラーに複数の名前でアクセスすることも可能であり、異なるデフォルトオプションを指定したい場合に便利です。

単一の統合更新リクエストハンドラーは、XML、CSV、JSON、およびjavabinの更新リクエストをサポートし、ContentStreamのContent-Typeに基づいて適切なContentStreamLoaderに委任します。

ドキュメントをロードした後、インデックスされる前にドキュメントを前処理する必要がある場合（スキーマに対してチェックされる前でも）、SolrにはUpdate Request Handler用のドキュメント前処理プラグインがあります。これらはUpdate Request Processorと呼ばれ、デフォルトやカスタムの設定チェーンを可能にします。
## 更新リクエストハンドラーの設定


デフォルトの設定ファイルには、デフォルトで更新リクエストハンドラが設定されています。
```
<requestHandler name="/update" class="solr.UpdateRequestHandler" />
```

## XML形式のインデックスの更新


インデックス更新コマンドは、Content-type: application/xmlまたはContent-type: text/xmlを使用して、XMLメッセージとして更新ハンドラーに送信することができます。
### ドキュメントの追加


ドキュメントを追加するための更新ハンドラで認識されるXMLスキーマは非常にわかりやすいです。
- The <add> element introduces one more documents to be added.
- The <doc> element introduces the fields making up a document.
- The <field> element presents the content for a specific field.


例えば：
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


addコマンドは、指定できるいくつかのオプション属性をサポートしています。  
**commitWithin**
|Optional|Default: none|
| :---: | :---: |
  
*指定されたミリ秒の間にドキュメントを追加してください。*  
**overwrite**
|Optional|Default: true|
| :---: | :---: |
  
*以下を参照し、同じドキュメントの以前のバージョンを上書きするかどうかを確認するためのユニークキー制約をチェックするかどうかを示します。*

もしドキュメントスキーマが一意のキーを定義している場合、/update操作でドキュメントを追加すると、同じ一意のキーを持つインデックス内のドキュメントが上書き（つまり置き換え）されます。
一意のキーが定義されていない場合、既存のドキュメントを置き換えるためのチェックが必要ないため、インデックスへのインデックスのパフォーマンスがやや高速になります。

もしユニークなキーフィールドを持っているが、一意性チェックを安全にバイパスすることができると確信している場合（例えば、インデックスをバッチで構築し、インデックスコードが同じドキュメントを2回以上追加しないことを保証している場合）、ドキュメントを追加する際にoverwrite="false"オプションを指定することができます。
### XML 更新コマンド

#### 更新中にコミットして最適化する


<commit>操作は、最後のコミット以降にロードされたすべてのドキュメントをディスク上の1つ以上のセグメントファイルに書き込みます。
コミットが発行される前は、新しくインデックスされたコンテンツは検索で見ることができません。
コミット操作は新しいサーチャーを開き、設定されているイベントリスナーをトリガーします。

コミットは<commit/>メッセージを明示的に発行することができ、solrconfig.xml内の<autocommit>パラメーターからもトリガーされることがあります。

<optimize>操作は、Solrに内部データ構造をマージするようリクエストします。
大きなインデックスの場合、最適化には完了までにかなりの時間がかかるかもしれませんが、多数の小さなセグメントファイルを大きなセグメントにマージすることで、検索パフォーマンスが向上する可能性があります。
多数のシステムに検索を分散するためにSolrのレプリケーションメカニズムを使用している場合は、最適化後に完全なインデックスを転送する必要があることに注意してください。  
:warning:Warning  
オプティマイズは、静的インデックス、つまり定期的な更新プロセスの一部として最適化できるインデックスにのみ使用することを検討すべきです（1日に1回の更新など）。
NRT機能を必要とするアプリケーションは、オプティマイズを使用すべきではありません。

<commit>と<optimize>要素は、これらのオプション属性を受け入れます。  
**waitSearcher**
|Optional|Default: true|
| :---: | :---: |
  
*新しい検索が開かれ、主なクエリ検索として登録されるまでブロックされ、変更が表示されるようになります。*  
**expungeDeletes**
|Optional|Default: false|
| :---: | :---: |
  
*10%以上の削除済みドキュメントを持つセグメントをマージし、その過程で削除済みドキュメントを完全に削除します。結果として得られるセグメントは、maxMergedSegmentMBを考慮します。このオプションは<commit>操作にのみ適用されます。*  
**maxSegments**
|Optional|Default: none|
| :---: | :---: |
  
*この数以下のセグメントにマージするために最善の努力をしますが、その目標が達成されることを保証するものではありません。セグメント数を最小限にすることが有益であるという具体的な証拠がない限り、このパラメータは省略し、デフォルトの動作を受け入れるべきです。このオプションは、<optimize操作でのみ適用されます。デフォルトは無制限で、マージされたセグメントはmaxMergedSegmentMBの設定を尊重します。*

ここには、オプション属性を使用した<commit>と<optimize>の例があります。
```
<commit waitSearcher="false"/>
<commit waitSearcher="false" expungeDeletes="true"/>
<optimize waitSearcher="false"/>
```

#### 削除操作


ドキュメントは2つの方法でインデックスから削除することができます。
「IDによる削除」は、指定されたIDを持つドキュメントを削除し、スキーマでUniqueIDフィールドが定義されている場合にのみ使用することができます。
子/ネストされたドキュメントに対しては機能しません。
「クエリによる削除」は、指定されたクエリに一致するすべてのドキュメントを削除しますが、commitWithinはクエリによる削除では無視されます。
単一の削除メッセージには複数の削除操作を含めることができます。
```
<delete>
  <id>0002166313</id>
  <id>0031745983</id>
  <query>subject:sport</query>
  <query>publisher:penguin</query>
</delete>
```
  
:exclamation:Important  
JoinクエリパーサーをDelete By Queryで使用する際には、ClassCastExceptionを回避するためにスコアパラメーターを値"none"で使用する必要があります。
スコアパラメーターの詳細については、Joinクエリパーサーのセクションを参照してください。
#### ロールバック操作


ロールバックコマンドは、最後のコミット以降にインデックスに行われたすべての追加と削除を取り消します。
イベントリスナーを呼び出したり、新しいサーチャーを作成することはありません。
その構文は単純です：<rollback/>。
#### グループ化操作


1つのXMLファイルに複数のコマンドを投稿することができ、<update>要素でグループ化することができます。
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

### Curlを使用して更新を実行する方法


上記のコマンドを実行するために、curlユーティリティを使用することができます。curlコマンドに--data-binaryオプションを使用してXMLメッセージを追加し、HTTP POSTリクエストを生成します。
例えば、
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


XMLメッセージを含むファイルを投稿するには、代替フォームを使用することができます。
```
curl http://localhost:8983/solr/my_collection/update -H "Content-Type: text/xml" --data-binary @myfile.xml
```


上記のアプローチはうまく機能しますが、--data-binaryオプションを使用すると、curlがサーバーに投稿する前にmyfile.xml全体をメモリに読み込むため、問題が発生する可能性があります。
これは、複数ギガバイトのファイルを扱う際に問題が発生する場合があります。
次の代替curlコマンドは、同等の操作を行いますが、curlのメモリ使用量を最小限に抑えます。
```
curl http://localhost:8983/solr/my_collection/update -H "Content-Type: text/xml" -T "myfile.xml" -X POST
```


短い要求は、requestParsers要素のsolrconfig.xmlで有効になっている場合、HTTP GETコマンドを使用して送信することもできます。要求をURLエンコードし、次のように"<"と">"をエスケープすることに注意してください。
```
curl http://localhost:8983/solr/my_collection/update?stream.body=%3Ccommit/%3E&wt=xml
```


Solrからの応答は、以下に示す形式を取ります。
```
<response>
  <lst name="responseHeader">
    <int name="status">0</int>
    <int name="QTime">127</int>
  </lst>
</response>
```


ステータスフィールドは、失敗の場合にはゼロ以外の値になります。
### XMLインデックスの更新を行うためにXSLTを使用する。


スクリプティングモジュールには、任意のXMLをインデックスするために<tr>パラメータを使用してXSL変換を適用することができる独立したXSLTアップデートリクエストハンドラが用意されています。
configsetのconf/xsltディレクトリに、受信データを期待される<add><doc/></add>形式に変換することができるXSLTスタイルシートが必要であり、trパラメータを使用してそのスタイルシートの名前を指定する必要があります。

この機能を使用する前に、スクリプトモジュールを有効にする必要があります。
### トランスレートパラメーター


XSLTアップデートリクエストハンドラーは、trパラメーターを受け入れます。このパラメーターは、使用するXML変換を識別します。
変換は、Solrのconf/xsltディレクトリにある必要があります。
### XSLTの設定


以下の例は、Solrディストリビューションのsample_techproducts_configs configsetからXSLT Update Request Handlerがどのように設定されているかを示しています。
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


xsltCacheLifetimeSecondsの値が5であれば、XSLTの変更を素早く確認するために開発には良いでしょう。本番環境では、おそらくより高い値を設定することが望ましいでしょう。
### XSLTアップデートの例


以下は、標準のSolr XML出力をSolrが期待する<add><doc/></add>形式に変換するためのサンプル_techproducts_configs/conf/xslt/updateXml.xsl XSLファイルです。
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


このスタイルシートは、SolrのXML検索結果フォーマットをSolrのUpdate XML構文に変換します。例えば、すべてのフィールドが保存されていることが前提となる別のSolrファイルにインデックスできる形式に、Solr 1.3のインデックス（CSVレスポンスライターがない）をコピーすることができます。
```
$ curl -o standard_solr_xml_format.xml "http://localhost:8983/solr/techproducts/select?q=ipod&fl=id,cat,name,popularity,price,score&wt=xml"

$ curl -X POST -H "Content-Type: text/xml" -d @standard_solr_xml_format.xml "http://localhost:8983/solr/techproducts/update/xslt?commit=true&tr=updateXml.xsl"
```
  
:information_source:Note  
Response Writer XSLTの例では、trパラメータを使用することで、反対のエクスポート/インポートサイクルを見ることができます。
## JSON形式のインデックス更新


Solrは定義された構造に準拠するJSONを受け入れることができます。また、任意のJSON形式のドキュメントを受け入れることもできます。
任意の形式のJSONを送信する場合、更新リクエストと一緒に送信する必要がある追加パラメータがあります。これらのパラメータについては、セクション「カスタムJSONの変換とインデックス化」で説明されています。
### SolrスタイルのJSON


JSON形式の更新リクエストは、Content-Type: application/jsonまたはContent-Type: text/jsonを使用してSolrの/updateハンドラーに送信することができます。

JSON形式の更新は、以下で詳しく説明する3つの基本形式があります。
- A single document, expressed as a top level JSON Object.
To differentiate this from a set of commands, the json.command=false request parameter is required.
- A list of documents, expressed as a top level JSON Array containing a JSON Object per document.
- A sequence of update commands, expressed as a top level JSON Object (a Map).

#### 単一のJSONドキュメントを追加する


JSONを使用してドキュメントを追加する最も簡単な方法は、各ドキュメントをJSONオブジェクトとして個別に送信することです。 /update/json/docsパスを使用してください。
```
curl -X POST -H 'Content-Type: application/json' 'http://localhost:8983/solr/my_collection/update/json/docs' --data-binary '
{
  "id": "1",
  "title": "Doc 1"
}'
```

#### 複数のJSONドキュメントの追加


JSONを使用して複数のドキュメントを一度に追加することは、各オブジェクトがドキュメントを表すJSONオブジェクトのJSON配列を介して行うことができます。
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


サンプルのJSONファイルは、example/exampledocs/books.jsonに提供されており、オブジェクトの配列を含んでいます。これらは、Solrの「techproducts」例に追加することができます。
```
curl 'http://localhost:8983/solr/techproducts/update?commit=true' --data-binary @example/exampledocs/books.json -H 'Content-type:application/json'
```

#### JSONアップデートコマンドを送信する。


一般的に、JSONの更新構文は、XMLの更新ハンドラがサポートするすべての更新コマンドを、直接的なマッピングを通してサポートします。
複数のコマンド、ドキュメントの追加や削除が、1つのメッセージに含まれる場合があります。
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


他のアップデートハンドラーと同様に、commit、commitWithin、optimize、およびoverwriteなどのパラメーターは、メッセージの本文ではなくURLに指定することもできます。

JSONのアップデートフォーマットでは、簡単なIDによる削除が可能です。
削除の値は、削除される特定のドキュメントIDのリスト（範囲ではなく）を含む配列になります。
例えば、単一のドキュメント:
```
{ "delete":"myid" }
```


またはドキュメントIDのリスト：
```
{ "delete":["id1","id2"] }
```


注：IDによる削除は子/ネストドキュメントに対して機能しません。

各「削除」に_version_を指定することもできます。
```
{
  "delete":"id":50,
  "_version_":12345
}
```


アップデートリクエストの本文でも、削除のバージョンを指定することができます。
### JSONの更新便利パス


Solrには、/updateハンドラーに加えて、いくつかの追加のJSON固有のリクエストハンドラーのパスがデフォルトで利用可能です。これらのパスは、いくつかのリクエストパラメーターの動作を暗黙的にオーバーライドします。

/update/jsonパスは、Content-Typeの設定が困難なアプリケーションからJSON形式の更新コマンドを送信するクライアントにとって便利な場合があります。一方、/update/json/docsパスは、個々のドキュメントまたはリストとして常に送信したいクライアントにとって、フルJSONコマンド構文を気にする必要がなく特に便利です。
### カスタムJSONドキュメント


SolrはカスタムJSONをサポートすることができます。
これは「カスタムJSONの変換とインデックス化」のセクションでカバーされています。
## CSV形式のインデックスの更新


CSV形式の更新リクエストは、Content-Type: application/csvまたはContent-Type: text/csvを使用して、Solrの/updateハンドラーに送信することができます。

「example/exampledocs/books.csv」には、Solrの「techproducts」例にいくつかのドキュメントを追加するために使用できるサンプルのCSVファイルが提供されています。
```
curl 'http://localhost:8983/solr/my_collection/update?commit=true' --data-binary @example/exampledocs/books.csv -H 'Content-type:application/csv'
```

### CSV更新パラメーター


CSVハンドラーは、URLのf.parameter.optional_fieldname=valueの形式で多数のパラメーターの指定を可能にします。

以下の表は、アップデートハンドラーのパラメーターを説明しています。  
**separator**
|Optional|Default: ,|
| :---: | :---: |
  
*フィールドの区切りとして使用される文字。このパラメータはグローバルであり、フィールドごとの使用については、分割パラメータを参照してください。*  
**trim**
|Optional|Default: false|
| :---: | :---: |
  
*もしtrueなら、値から前後の空白を削除します。このパラメータはグローバルまたはフィールドごとに設定することができます。*  
**header**
|Optional|Default: true|
| :---: | :---: |
  
*最初の入力行にフィールド名が含まれている場合はtrueに設定します。フィールド名パラメータが存在しない場合に使用されます。このパラメータはグローバルです。*  
**fieldnames**
|Optional|Default: none|
| :---: | :---: |
  
*ドキュメントを追加する際に使用するフィールド名のコンマ区切りリスト。このパラメーターはグローバルです。*  
**literal.field_name**
|Optional|Default: none|
| :---: | :---: |
  
*指定されたフィールド名のための文字通りの値。このパラメータはグローバルです。*  
**skip**
|Optional|Default: none|
| :---: | :---: |
  
*スキップするフィールド名のコンマ区切りリストです。このパラメータはグローバルです。*  
**skipLines**
|Optional|Default: 0|
| :---: | :---: |
  
*入力ストリームでCSVデータが始まる前に破棄する行数の数、ヘッダーがある場合はそれも含める。このパラメーターはグローバルです。*  
**encapsulator**
|Optional|Default: none|
| :---: | :---: |
  
*文字列を囲むために使用されるオプションの文字は、CSVの区切り記号や空白などの文字を保持するために使用されます。この標準的なCSV形式では、囲み文字が囲まれた値内に現れる場合には、囲み文字を二重にすることで処理されます。*  
**escape**
|Optional|Default: none|
| :---: | :---: |
  
*CSVセパレーターまたは他の予約文字をエスケープするために使用される文字。エスケープが指定されている場合、ほとんどのフォーマットではカプセル化またはエスケープのどちらかが使用されるため、カプセル化も明示的に指定されていない限り使用されません。*  
**keepEmpty**
|Optional|Default: false|
| :---: | :---: |
  
*空の長さがゼロのフィールドを保持し、インデックス化します。このパラメーターはグローバルまたはフィールドごとに設定できます。*  
**map**
|Optional|Default: none|
| :---: | :---: |
  
*別の値に1つの値をマッピングします。フォーマットはmap=value:replacementです（replacementは空にすることもできます）。このパラメータはグローバルまたはフィールドごとに設定することができます。*  
**split**
|Optional|Default: none|
| :---: | :---: |
  
*もし真であれば、フィールドを個別のパーサーによって複数の値に分割します。このパラメータはフィールドごとに使用されます。例えば、f.FIELD_NAME_GOES_HERE.split=trueとなります。*  
**overwrite**
|Optional|Default: true|
| :---: | :---: |
  
*もし真であれば、Solrスキーマで宣言されたuniqueKeyフィールドに基づいて重複ドキュメントをチェックし上書きします。インデックスを作成するドキュメントに重複が含まれていないことがわかっている場合は、falseに設定することでかなりの高速化が見られるかもしれません。*  
**commit**
|Optional|Default: none|
| :---: | :---: |
  
*データが取り込まれた後、コミットを発行します。このパラメータはグローバルです。*  
**commitWithin**
|Optional|Default: none|
| :---: | :---: |
  
*指定されたミリ秒数内にドキュメントを追加してください。このパラメーターはグローバルです。*  
**rowid**
|Optional|Default: none|
| :---: | :---: |
  
*行番号（rowid）を、パラメータの値で指定されたフィールドにマップします。例えば、CSVに一意のキーがなく、行番号をそれとして使用したい場合は、このパラメータをグローバルに設定します。*  
**rowidOffset**
|Optional|Default: 0|
| :---: | :---: |
  
*ドキュメントに追加する前に、与えられたオフセット（整数として）をrowidに追加してください。このパラメータはグローバルです。*
### インデックスタブ区切りファイルの索引付け


CSVドキュメントをインデックスするのに使用される同じ機能は、タブ区切りファイル（TSVファイル）をインデックスするためにも簡単に使用することができ、さらにCSVのカプセル化ではなくバックスラッシュのエスケープを処理することもできます。

例えば、MySQLのテーブルをタブ区切りファイルにダンプすることができます。
```
SELECT * INTO OUTFILE '/tmp/result.txt' FROM mytable;
```


このファイルは、区切り文字をタブ（%09）に設定し、エスケープ文字をバックスラッシュ（%5c）に設定することで、Solrにインポートすることができます。
```
curl 'http://localhost:8983/solr/my_collection/update/csv?commit=true&separator=%09&escape=%5c' --data-binary @/tmp/result.txt
```

### CSVの更新の便利なパス


/updateハンドラーに加えて、Solrではデフォルトで追加のCSV専用のリクエストハンドラーパスが利用可能です。これは一部のリクエストパラメーターの挙動を暗黙的に上書きします。

/update/csvのパスは、コンテンツタイプの設定が難しいアプリケーションからCSV形式の更新コマンドを送信するクライアントにとって便利な場合があります。