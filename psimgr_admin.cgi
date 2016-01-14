#!/usr/bin/perl

# This script is copyright (c) 2014 by WebMO, LLC, all rights reserved.
# Its use is subject to the license agreement that can be found at the following
# URL:  http://www.webmo.net/license


use ParsedHTML;

$require++;
require("globals.cgi");
require("parse.cgi");
require("password.cgi");
require("redirect.cgi");
require("servercontrol.cgi");
require("interfacemgr_shared.cgi");
$require--;

if (!$require)
{
	local %form_data, %cookie_data;
	&parse_form_data(*form_data);
	&parse_cookie_data(*cookie_data);
		
	local $username = $cookie_data{'admin_username'};
	local $admin_group = &get_group($username);
	
	if (!&check_stored_password_admin() || $username ne 'admin')
	{
		&redirect("$url_cgiBase/login.cgi");
		exit(0);
	}

	local $operation = $form_data{'operation'};
	local $targetServer = $form_data{'targetServer'};
	local $server = $form_data{'server'};
	
	&validate_cpu_range(*form_data);
		
	if ($targetServer eq "")
	{
		$targetServer = (split(/,/, (split(/:/, $servers))[0]))[0];
		$targetServer = (split(/,/, $queues))[0] if ($externalBatchQueue);
	}
	
	&load_appropriate_interface("psi", $targetServer);
	
	if ($operation eq "ChangeGlobals")
	{
		my %serverInfo;
		&get_server_info($targetServer, \%serverInfo);
		if ($serverInfo{'localhost'} && !$externalBatchQueue &&
			(!-d $form_data{'psiBase'} || !-x "$form_data{'psiBase'}/bin/psi4"))
		{		
			$errorMsg = "<H2 CLASS='admin_failure'>No Psi installation found at specifed location</H2>";
		}
		else
		{
			&update_appropriate_interface("psi", $targetServer);
			$errorMsg = "<H2 CLASS='admin_success'>Configuration updated</H2>";
		}
	}
	elsif ($operation eq "ChangeServer")
	{
		$targetServer = $server;
		&load_appropriate_interface("psi", $targetServer);
	}
	elsif ($operation eq "Return")
	{
		$require++;
		require("interfacemgr_admin.cgi");
		$require--;
		&generate_interface_manager_page();
		exit(0);
	}
		
	&generate_psi_manager_page();
}


sub generate_psi_manager_page()
{
	my $parser = new ParsedHTML;	
	$parser->parse("$htmlBase/psimgr_admin.html") || die "Cannot open HTML file: $!", ;
}

1;
