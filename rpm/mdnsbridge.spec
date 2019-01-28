%global module_name mdnsbridge

Name: 			python-%{module_name}
Version: 		0.6.1
Release: 		1%{?dist}
License: 		Internal Licence
Summary: 		mDNS to HTTP bridge service

Source0: 		%{module_name}-%{version}.tar.gz
Source1:		ips-api-mdnsbridge.conf
Source2:		python-mdnsbridge.service

BuildArch:      noarch

BuildRequires:	python2-devel
BuildRequires:  python-setuptools
BuildRequires:	systemd

Requires:       python
Requires:       ips-reverseproxy-common
Requires:	nmoscommon
Requires:       systemd-python
%{?systemd_requires}

%description
mDNS to HTTP bridge service

%prep
%setup -n %{module_name}-%{version}

%build
%{py2_build}

%install
%{py2_install}

# Install systemd unit file
install -D -p -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/python-mdnsbridge.service

# Install Apache config file
install -D -p -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/httpd/conf.d/ips-apis/nmos-api-mdnsbridge-v1_0.conf


%post
%systemd_post python-mdnsbridge.service
systemctl start nmos-mdnsbridge
systemctl reload httpd


%preun
systemctl stop nmos-mdnsbridge

%clean
rm -rf %{buildroot}

%files
%{_bindir}/nmos-mdnsbridge

%{_unitdir}/%{name}.service

%{python2_sitelib}/%{module_name}
%{python2_sitelib}/%{module_name}-%{version}*.egg-info

%defattr(-,ipstudio, ipstudio,-)
%config %{_sysconfdir}/httpd/conf.d/ips-apis/nmos-api-mdnsbridge-v1_0.conf

%changelog
* Fri Nov 10 2017 Simon Rankine <Simon.Rankine@bbc.co.uk> - 0.1.0-2
- Re-packaging for open sourcing
* Tue Apr 25 2017 Sam Nicholson <sam.nicholson@bbc.co.uk> - 0.1.0-1
- Initial packaging for RPM
