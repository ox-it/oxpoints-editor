<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output indent="yes"/>

  <xsl:template match="/">
    <metadata>
      <!--
      <title>
        <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName)[not(@type) or @type='' or contains(tokenize(@type, '\s'), 'preferred')][position()=1]"/>
      </title>
      -->
      <title>
        <xsl:choose>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[not(@type) or @type='' or contains(@type, 'preferred')]">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[not(@type) or @type='' or contains(@type, 'preferred')][position()=1]"/>
          </xsl:when>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[position()=1]"/>
          </xsl:when>
          <xsl:otherwise/>
        </xsl:choose>
      </title>
      <sort_title>
        <xsl:choose>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[contains(@type, 'sort')]">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[contains(@type, 'sort')][position()=1]"/>
          </xsl:when>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName | tei:object/tei:objectName)[position()=1]"/>
          </xsl:when>
          <xsl:otherwise/>
        </xsl:choose>
      </sort_title>

      <root_elem>
        <xsl:value-of select="name(*)"/>
      </root_elem>

      <type>
        <xsl:choose>
          <xsl:when test="*/@type">
            <xsl:value-of select="*/@type"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="*/tei:trait[@type='type']/tei:desc"/>
          </xsl:otherwise>
        </xsl:choose>
      </type>
      <dt_from>
        <xsl:value-of select="*/@from"/>
      </dt_from>
      <dt_to>
        <xsl:value-of select="*/@to"/>
      </dt_to>
      <homepage>
        <xsl:value-of select="(tei:org | tei:place)/tei:trait[@type='url']/tei:desc/tei:ptr/@target"/>
      </homepage>
      <address>
        <xsl:for-each select="(tei:org | tei:place)/tei:location/tei:address[1]/tei:addrLine">
          <xsl:value-of select="concat(., '&#xA;')"/>
        </xsl:for-each>
        <xsl:value-of select="(tei:org | tei:place)/tei:location/tei:address[1]/tei:postCode"/>
      </address>
      <idno_oucs>
        <xsl:value-of select="tei:org/tei:idno[@type='oucs']"/>
      </idno_oucs>
      <idno_estates>
        <xsl:value-of select="tei:place/tei:idno[@type='obn']"/>
      </idno_estates>
      <idno_finance>
        <xsl:value-of select="tei:org/tei:idno[@type='finance']"/>
      </idno_finance>
      <longitude>
        <xsl:value-of select="substring-before(tei:place/tei:location/tei:geo, ' ')"/>
      </longitude>
      <latitude>
        <xsl:value-of select="substring-after(tei:place/tei:location/tei:geo, ' ')"/>
      </latitude>

        <linking_you>
            <xsl:for-each
                    select="*/tei:group[@type='lyou']/tei:trait[starts-with(@type, 'lyou:') and tei:desc/tei:ptr/@target]">
                <xsl:if test="position() &gt; 1">
                    <xsl:text> </xsl:text>
                </xsl:if>
                <xsl:value-of select="substring-after(@type, 'lyou:')"/>
            </xsl:for-each>
        </linking_you>
    </metadata>

  </xsl:template>

</xsl:stylesheet>

