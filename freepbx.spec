%define	name	freepbx
%define	version	2.9.0
%define	release	%mkrel 1

%define _requires_exceptions php-asmanager.php
%define	build_postinstall	0
%define	build_sqlite		1
%{?_with_postinstall:	%global build_postinstall 1}
%{?_without_sqlite:	%global build_sqlite 0}

Summary:	Is an easy to use GUI that controls and manages Asterisk
Name:		freepbx
Version:	%{version}
Release:	%{release}
License:	GPL
Group:		System/Servers
Source:		http://mirror.freepbx.org/%{name}-%{version}.tar.gz
Patch1:		amportal-conf.patch
Patch2:		install-md5check.patch
Patch3:		asterisk-runas.patch
Patch4:		ignore-selinux.patch
BuildRoot:	%{_tmppath}/%{name}-%{version}-root
BuildArch:	noarch
URL:		http://www.freepbx.org
Requires:	asterisk
Requires:	apache
Requires:	apache-mod_php
Requires:	php-pear-DB
Requires:	asterisk-extra-sounds
%if %build_sqlite
BuildRequires:	sqlite3-tools
Requires:	asterisk-plugins-sqlite
Requires:	php-sqlite3
%else
Requires:	asterisk-addons
Requires:	php-mysql
Requires:	mysql-server
%endif

%description
FreePBX is an easy to use GUI (graphical user interface) that controls and 
manages Asterisk, the world's most popular open source telephony engine 
software. FreePBX has been developed and hardened by thousands of 
volunteers over tens of thousands man hours. FreePBX has been downloaded 
over 3,000,000 times and claims over 300,000 active phone systems. 
If you don't know about FreePBX, you are probably paying too much for 
your phone system. 

%prep
%setup -q -n %{name}-%{version}

%patch1 -p0
%patch2 -p0
# Have to start Asterisk as root before fixing permissions..
%patch3 -p0
%patch4 -p0

%build

%install
rm -rf %{buildroot}

# This *really* needs to change at some point.
mkdir -p %{buildroot}/usr/src/%{name}-%{version}/
cp -r * %{buildroot}/usr/src/%{name}-%{version}/
mkdir -p %{buildroot}/var/lib/asterisk/
cat SQL/newinstall.sqlite3.sql | sqlite3 %{buildroot}/var/lib/asterisk/freepbx.db

%post

%if %build_postinstall
dbuser="root"
dbpass=""
mysqlcmd="mysql --user=${dbuser} --password=${dbpass}"
mysqladmcmd="mysqladmin --user=${dbuser} --password=${dbpass}"

# Just in case they aren't running.
usermod -a -G asterisk apache
service httpd start
chkconfig httpd on

%if %build_sqlite

./start_asterisk start
./install_amp
# This would be installed on the system, but may not be in $PATH
./amp_conf/sbin/amportal start
./amp_conf/bin/module_admin reload

amportal=/usr/sbin/amportal
if ! grep -c amportal /etc/rc.local > /dev/null; then
	echo "${amportal} start" >> /etc/rc.local
fi

%else
if ! ${mysqlcmd} --execute "quit" > /dev/null 2>&1; then
	echo "Failed to connect to mysql with user '${dbuser}' and password '${dbpass}'."
	exit 1
else
	cd /usr/src/%{name}-%{version}/

	if [ ! -f /etc/amportal.conf ]; then
		install -m 660 amportal.conf /etc/amportal.conf
		chown asterisk:asterisk /etc/amportal.conf
	else
		if ! grep "^AMPVMUMASK=" /etc/amportal.conf >/dev/null; then
			echo "Adding AMPVMUMASK option to existing /etc/amportal.conf"
			echo "AMPVMUMASK=007" >> /etc/amportal.conf
		fi
	fi
	if ! ${mysqlcmd} --database asterisk --execute "show tables" > /dev/null 2>&1; then
		${mysqladmcmd} create asterisk
		${mysqlcmd} --database asterisk < SQL/newinstall.sql
		${mysqlcmd} --execute "GRANT ALL PRIVILEGES ON asterisk.* TO freepbx@localhost IDENTIFIED BY 'fpbx';"
	fi

	if ! ${mysqlcmd} --database asteriskcdrdb --execute "show tables" > /dev/null 2>&1; then
		${mysqladmcmd} create asteriskcdrdb
		${mysqlcmd} --database asteriskcdrdb < SQL/cdr_mysql_table.sql
		${mysqlcmd} --execute "GRANT ALL PRIVILEGES ON asteriskcdrdb.* TO freepbx@localhost IDENTIFIED BY 'fpbx';"
	fi
	./start_asterisk start
	./install_amp
	# This would be installed on the system, but may not be in $PATH
	./amp_conf/sbin/amportal start
	./amp_conf/bin/module_admin reload

	amportal=/usr/sbin/amportal
	if ! grep -c amportal /etc/rc.local > /dev/null; then
		echo "${amportal} start" >> /etc/rc.local
	fi
fi
%endif
%else
echo "Please install the FreePBX webroot and framework with install_amp script in /usr/src/%{name}-%{version} directory. More information in INSTALL file."
%endif

%postun
echo "The FreePBX uninstallation procedure is non-existent.  You will need to manually remove left-over files from Apache webroot."

%clean
rm -rf %{buildroot}

%files
%defattr(-, root, root)
%doc CHANGES CONTRIB.txt FAQ INSTALL UPGRADE
%if %build_sqlite
%attr(660,asterisk,asterisk) %config(noreplace) /var/lib/asterisk/freepbx.db
%endif
/usr/src/%{name}-%{version}



%changelog
* Wed Jun 15 2011 Lonyai Gergely <aleph@mandriva.org> 2.9.0-1mdv2011.0
+ Revision: 685395
- 2.9.0
  Drop sqlite patch

* Fri Mar 25 2011 Luis Daniel Lucio Quiroz <dlucio@mandriva.org> 2.8.1-1
+ Revision: 648468
- 2.8.1 for asterisk 1.8

* Sun Dec 05 2010 Oden Eriksson <oeriksson@mandriva.com> 2.7.0-3mdv2011.0
+ Revision: 610767
- rebuild

* Mon Apr 05 2010 Lonyai Gergely <aleph@mandriva.org> 2.7.0-2mdv2010.1
+ Revision: 531529
- _requires_exceptions php-asmanager.php

* Fri Mar 26 2010 Lonyai Gergely <aleph@mandriva.org> 2.7.0-1mdv2010.1
+ Revision: 527689
- 2.7.0
  Bugfix: #58377 - freepbx has unsatisfied requires

* Wed Feb 03 2010 Lonyai Gergely <aleph@mandriva.org> 2.6.0-2mdv2010.1
+ Revision: 499935
- Fix typo (asterisk-extra-sounds) in Requiements.
- 2.6.0

* Mon Nov 09 2009 Lonyai Gergely <aleph@mandriva.org> 2.5.2-1mdv2010.1
+ Revision: 463440
- 2.5.2

* Mon Aug 24 2009 Lonyai Gergely <aleph@mandriva.org> 2.5.1-1mdv2010.0
+ Revision: 420294
- fix release tag
- initial packages
 - TODO: create a init script and integrate to asterisk init solution
- create freepbx

