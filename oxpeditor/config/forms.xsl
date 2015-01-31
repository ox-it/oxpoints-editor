<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
        xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output indent="yes"/>

  <xsl:template name="path-attribute">
    <xsl:attribute name="path">
      <xsl:for-each select="ancestor-or-self::*[position()!=last()]">
        <xsl:variable name="name" select="name()"/>
        <xsl:if test="name() != 'root'">
          <xsl:value-of select="name()"/>
            <xsl:text>[</xsl:text>
            <xsl:value-of select="count(preceding-sibling::*[name() = $name]) + 1"/>
            <xsl:text>]</xsl:text>
          <xsl:if test="not(position()=last())">
            <xsl:text>/</xsl:text>
          </xsl:if>
        </xsl:if>
      </xsl:for-each>
    </xsl:attribute>
    <xsl:copy-of select="@ignore"/>
  </xsl:template>

  <xsl:template match="/">
    <forms oxpid="{/*/@oxpID}">
      <form-types>
        <xsl:if test="tei:org | tei:place">
          <form-type name="NameForm"/>
          <form-type name="IDNoForm"/>
          <form-type name="AddressForm"/>
          <form-type name="URLForm"/>
          <form-type name="DescriptionForm"/>
        </xsl:if>
        <xsl:if test="tei:place">
          <form-type name="LocationForm"/>
        </xsl:if>
        <xsl:if test="*[@type='Room' or @type='Space' or tei:trait[@type='type']/desc/text() = 'Room' or tei:trait[@type='type']/desc/text() = 'Space']">
          <form-type name="SpaceConfigurationForm"/>
        </xsl:if>
      </form-types>
      <xsl:apply-templates select="tei:org | tei:place"/>
    </forms>
  </xsl:template>

  <xsl:template match="tei:org | tei:place">
    <xsl:for-each select="tei:orgName | tei:placeName">
      <form name="NameForm">
        <xsl:call-template name="path-attribute"/>
        <value>
          <xsl:value-of select="."/>
        </value>
        <type_preferred>
          <xsl:if test="not(@type) or @type='' or contains(@type, 'preferred')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_preferred>
        <type_sort>
          <xsl:if test="contains(@type, 'sort')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_sort>
        <type_alternate>
          <xsl:if test="contains(@type, 'alternate')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_alternate>
        <type_hidden>
          <xsl:if test="contains(@type, 'hidden')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_hidden>
        <type_short>
          <xsl:if test="contains(@type, 'short')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_short>
        <type_acronym>
          <xsl:if test="contains(@type, 'acronym')">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_acronym>
        <type_map>
          <xsl:if test="contains(@type, 'map') and self::tei:placeName">
            <xsl:text>on</xsl:text>
          </xsl:if>
        </type_map>
              
      </form>
    </xsl:for-each>

    <xsl:for-each select="tei:idno">
      <form name="IDNoForm">
        <xsl:call-template name="path-attribute"/>
        <value>
          <xsl:value-of select="."/>
        </value>
        <scheme>
          <xsl:value-of select="@type"/>
        </scheme>
      </form>
    </xsl:for-each>

    <xsl:for-each select="tei:location[tei:address]">
      <form name="AddressForm">
        <xsl:call-template name="path-attribute"/>
        <street>
          <xsl:value-of select="tei:address/tei:addrLine[position()=1]"/>
        </street>
        <extended>
          <xsl:if test="tei:address/tei:addrLine[position()=3]">
            <xsl:value-of select="tei:address/tei:addrLine[position()=2]"/>
          </xsl:if>
        </extended>
        <locality>
          <xsl:if test="tei:address/tei:addrLine[position()=2]">
            <xsl:value-of select="tei:address/tei:addrLine[position()=last()]"/>
          </xsl:if>
        </locality>
        <postcode>
          <xsl:value-of select="tei:address/tei:postCode"/>
        </postcode>
      </form>
    </xsl:for-each>

    <xsl:for-each select="tei:location[tei:geo]">
      <form name="LocationForm">
        <xsl:call-template name="path-attribute"/>
        <longitude>
          <xsl:value-of select="substring-before(tei:geo, ' ')"/>
        </longitude>
        <latitude>
          <xsl:value-of select="substring-after(tei:geo, ' ')"/>
        </latitude>
      </form>
    </xsl:for-each>

    <xsl:for-each select="tei:trait[tei:desc/tei:ptr]">
      <form name="URLForm">
        <xsl:call-template name="path-attribute"/>
        <url>
          <xsl:value-of select="tei:desc/tei:ptr/@target"/>
        </url>
        <ptype>
          <xsl:value-of select="@type"/>
        </ptype>
      </form>
    </xsl:for-each>

<!--
    <xsl:for-each select="tokenize(@equiv, '\s+')">
      <form name="URLForm" path="@equiv[{position()}]">
        <url>
          <xsl:value-of select="."/>
        </url>
        <ptype>equiv</ptype>
      </form>
    </xsl:for-each>
-->

    <xsl:for-each select="tei:desc">
      <form name="DescriptionForm">
        <xsl:call-template name="path-attribute"/>
        <description>
          <xsl:value-of select="."/>
        </description>
      </form>
    </xsl:for-each>

    <xsl:for-each select="tei:trait[@type='configuration']">
      <form name="SpaceConfigurationForm">
        <xsl:call-template name="path-attribute"/>
        <type>
          <xsl:value-of select="@subtype"/>
        </type>
        <capacity>
          <xsl:value-of select="tei:note[@type='capacity']"/>
        </capacity>
        <comment>
          <xsl:value-of select="tei:note[@type='comment']"/>
        </comment>
      </form>
    </xsl:for-each>
        

  </xsl:template>
</xsl:stylesheet>
