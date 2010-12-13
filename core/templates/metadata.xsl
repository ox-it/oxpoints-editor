<?xml version="1.0"?>
<xsl:stylesheet version="2.0"
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
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName)[not(@type) or @type='' or contains(@type, 'preferred')]">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName)[not(@type) or @type='' or contains(@type, 'preferred')][position()=1]"/>
          </xsl:when>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName)">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName)[position()=1]"/>
          </xsl:when>
          <xsl:otherwise/>
        </xsl:choose>
      </title>
      <sort_title>
        <xsl:choose>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName)[contains(@type, 'sort')]">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName)[contains(@type, 'sort')][position()=1]"/>
          </xsl:when>
          <xsl:when test="(tei:org/tei:orgName | tei:place/tei:placeName)">
            <xsl:value-of select="(tei:org/tei:orgName | tei:place/tei:placeName)[position()=1]"/>
          </xsl:when>
          <xsl:otherwise/>
        </xsl:choose>
      </sort_title>

      <root_elem>
        <xsl:value-of select="name(*)"/>
      </root_elem>

      <type>
        <xsl:choose>
          <xsl:when test="(tei:org | tei:place)/@type">
            <xsl:value-of select="(tei:org | tei:place)/@type"/>
          </xsl:when>
          <xsl:otherwise>
            <xsl:value-of select="(tei:org | tei:place)/tei:trait[@type='type']/tei:desc"/>
          </xsl:otherwise>
        </xsl:choose>
      </type>
      <dt_from>
        <xsl:value-of select="(tei:org | tei:place)/@from"/>
      </dt_from>
      <dt_to>
        <xsl:value-of select="(tei:org | tei:place)/@to"/>
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
    </metadata>

  </xsl:template>

</xsl:stylesheet>

