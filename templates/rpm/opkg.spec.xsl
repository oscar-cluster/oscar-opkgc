<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

<xsl:import href="/tmp/opkgc/param.xsl" />

<xsl:output method ="text" encoding="us-ascii" />

<xsl:template match="/">

<xsl:for-each select="oscar">

Summary:        <xsl:value-of select="summary"/>
Name:           <xsl:value-of select="name"/>
Version:        <xsl:value-of select="version/major"/>.<xsl:value-of select="version/minor"/>
Release:        <xsl:value-of select="version/release"/>
Vendor:         Open Cluster Group &lt;http://OSCAR.OpenClusterGroup.org/&gt;
Distribution:   OSCAR
Packager:       <xsl:value-of select="packager/name"/> <xsl:value-of select="packager/email"/>
License:        <xsl:value-of select="license"/>
Group:          <xsl:value-of select="group"/>
Source:         %{name}.tar.gz
BuildRoot:      %{_localstatedir}/tmp/%{name}-root
BuildArch:      noarch
Depends:        %{name}-api, %{name}-server

%package api
Summary:        <xsl:value-of select="summary"/>, API part
Vendor:         Open Cluster Group &lt;http://OSCAR.OpenClusterGroup.org/&gt;
Distribution:   OSCAR
Packager:       <xsl:value-of select="packager/name"/> <xsl:value-of select="packager/email"/>
License:        <xsl:value-of select="license"/>
Group:          <xsl:value-of select="group"/>
BuildArch:      noarch
<xsl:for-each select="binary-package-list"><xsl:if test="not(filter/group)">Requires:       <xsl:for-each select="pkg"><xsl:value-of select="."/><xsl:if test="position() != last()">, </xsl:if>
</xsl:for-each>
</xsl:if></xsl:for-each>

%package server
Summary:        <xsl:value-of select="summary"/>, server part
Vendor:         Open Cluster Group &lt;http://OSCAR.OpenClusterGroup.org/&gt;
Distribution:   OSCAR
Packager:       <xsl:value-of select="packager/name"/> <xsl:value-of select="packager/email"/>
License:        <xsl:value-of select="license"/>
Group:          <xsl:value-of select="group"/>
<xsl:for-each select="binary-package-list">
<xsl:choose>
<xsl:when test="filter/group = 'oscar_server'">
Requires:       <xsl:for-each select="pkg"><xsl:value-of select="."/><xsl:if test="position() != last()">, </xsl:if></xsl:for-each>
</xsl:when>
</xsl:choose>
</xsl:for-each>
BuildArch:      noarch

%package client
Summary:        <xsl:value-of select="summary"/>, client part
Vendor:         Open Cluster Group &lt;http://OSCAR.OpenClusterGroup.org/&gt;
Distribution:   OSCAR
Packager:       <xsl:value-of select="packager/name"/> <xsl:value-of select="packager/email"/>
License:        <xsl:value-of select="license"/>
Group:          <xsl:value-of select="group"/>
<xsl:for-each select="binary-package-list">
<xsl:choose>
<xsl:when test="filter/group = 'oscar_clients'">
Requires:       <xsl:for-each select="pkg"><xsl:value-of select="."/><xsl:if test="position() != last()">, </xsl:if></xsl:for-each>
</xsl:when>
</xsl:choose>
</xsl:for-each>
BuildArch:      noarch

%description
OSCAR Package - <xsl:value-of select="description"/>

%description api
OSCAR Package - <xsl:value-of select="description"/>. API part.

%description server
OSCAR Package - <xsl:value-of select="description"/>. Server part.

%description client
OSCAR Package - <xsl:value-of select="description"/>. Client part.

%prep
%setup -n %{name}

%files api
%defattr(-,root,root)
%{prefix}/testing
%{prefix}/scripts
%{prefix}/config.xml

</xsl:for-each>

</xsl:template>
</xsl:stylesheet>
