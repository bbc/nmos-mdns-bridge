Name: 			nmosmdnsbridge
Version: 		0.1.0
Release: 		1%{?dist}
License: 		Internal Licence
Summary: 		mDNS to HTTP bridge service

Source0: 		%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:	python2-devel
BuildRequires:  python-setuptools
BuildRequires:  nmoscommon
BuildRequires:	systemd

Requires:       python
Requires:       nmos-reverse-proxy
Requires:		nmoscommon
%{?systemd_requires}

%description
mDNS to HTTP bridge service

%prep
%setup -n %{name}-%{version}

%build
%{py2_build}

%install
%{py2_install}

# Install systemd unit file
install -D -p -m 0644 debian/mdns-bridge.service %{buildroot}%{_unitdir}/nmos-mdnsbridge.service

# Install Apache config file
install -D -p -m 0644 etc/apache2/sites-available/nmos-api-mdnsbridge-v1_0.conf %{buildroot}%{_sysconfdir}/httpd/conf.d/nmos-apis/nmos-api-mdnsbridge-v1_0.conf


%post
%systemd_post nmos-mdnsbridge.service
systemctl start nmos-mdnsbridge
systemctl reload httpd


%preun
systemctl stop nmos-mdnsbridge

%clean
rm -rf %{buildroot}

%files
%{_bindir}/nmos-mdnsbridge

%{_unitdir}/nmos-mdnsbridge.service

%{python2_sitelib}/mdnsbridge
%{python2_sitelib}/nmosmdnsbrdige-%{version}*.egg-info

%defattr(-,ipstudio, ipstudio,-)
%config %{_sysconfdir}/httpd/conf.d/nmos-apis/nmos-api-mdnsbridge-v1_0.conf

%changelog
* Fri Nov 10 2017 Simon Rankine <Simon.Rankine@bbc.co.uk> - 0.1.0-2
- Re-packaging for open sourcing
* Tue Apr 25 2017 Sam Nicholson <sam.nicholson@bbc.co.uk> - 0.1.0-1
- Initial packaging for RPM
