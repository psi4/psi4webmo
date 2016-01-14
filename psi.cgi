#!/usr/bin/perl

# This script is copyright (c) 2014 by WebMO, LLC, all rights reserved.
# Its use is subject to the license agreement that can be found at the following
# URL:  http://www.webmo.net/license


use ParsedHTML;

$require++;
require("globals.cgi");
require("engine_shared.cgi");
require("checkpoint.cgi");
require("parse_psi.cgi");
$require--;

if (!$require)
{
	&process_engine_form_data('psi');
}

#when you want to add new properties add their name here
#and a corresponding parse_psi_PROPERTY to parse_psi.cgi
sub process_psi_output
{
	my ($jobNumber) = @_;
	my @properties = ('geometry_sequence', 'symmetry', 'basis', 'energy', 'dipole_moment', 'partial_charges', 'vibrational_modes', 'orbitals','force','scan');
	return &process_engine_output($jobNumber, 'psi', 'out', \@properties);
}

sub submit_psi_job
{
	&submit_engine_job('psi', 'inp', 'out');
}

sub do_psi_presubmit()
{
	my ($jobNumber) = @_;
	#create output.chk directory, if need
	mkdir("$currentUserBase/$jobNumber/output.chk", 0755) if ($saveCheckpointFile);
	#copy the checkpoint file, if needed
	if ($checkpointFile ne "")
	{
		# move the checkpoint file
		system("$cpPath -r $currentUserBase/$checkpointFile/output.chk $currentUserBase/$jobNumber");
		# copy the connections
		&copy("$currentUserBase/$checkpointFile/connections", "$currentUserBase/$jobNumber/connections");
	}
}

sub import_psi_job
{
	my($jobName, $path) = @_;
	&import_engine_job($jobName, $path, 'psi', 'out');
}

sub read_psi_form_data
{
	my @form_variables = keys %form_data;
	&read_engine_form_data('psi', \@form_variables);

  $scanInc = ($scanStop-$scanStart)/$scanSteps if ($scanSteps != 0);
  $scanInc2 = ($scanStop2-$scanStart2)/$scanSteps2 if ($scanSteps2 != 0);

  &add_sandboxed_var('scanInc', \$scanInc);
  &add_sandboxed_var('scanInc2', \$scanInc2);

	($geometry,$zvars) = split(/\n\n\s*/, $geometry);
	chomp $geometry;
	if ($cartesianCoordinates eq "on")
	{
		$geometry = "$geometry";
	}
	else
	{
		$geometry = "$geometry\n$zvars";
	}
}

1;
