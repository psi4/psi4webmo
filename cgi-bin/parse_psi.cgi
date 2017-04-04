#!/usr/bin/perl

# This script is copyright (c) 2014 by WebMO, LLC, all rights reserved.
# Its use is subject to the license agreement that can be found at the following
# URL:  http://www.webmo.net/license


$require++;
require("parse_output.cgi");
require("parse_molden.cgi");
$require--;

use FailureCodes;

#From NIST database of physical constants; http://physics.nist.gov/cgi-bin/cuu/Value?bohrrada0|search_for=bohr
my $bohrRadius = 0.5291772083; # Angstroms

sub parse_psi_version
{
  local (*logfileText) = @_;

  my $i = search_from_beginning('PSI4: An Open-Source Ab Initio Electronic Structure Package|Psi4: An Open-Source Ab Initio Electronic Structure Package', \@logfileText);
  return "" if ($i == -1);
  $i += 1;

  $_ = $logfileText[$i];
  chomp;

  #($version) = $_ =~ m/PSI\d* (.*) Driver/i;
  ($version) = $_ =~ m/Psi\d* (.*)/i;
  return $version;

}

sub parse_psi_normal_termination
{
  local (*logfileText) = @_;
  return &search_from_end('PSI4 exiting successfully|Psi4 exiting successfully', \@logfileText) != -1;
}

sub parse_psi_failure_code
{
  local (*logfileText) = @_;
  return $FailureCodes::UnknownFailure;
}

sub parse_psi_cpu_time
{
  local (*logfileText) = @_;
  my $cpu_time;
  my $i = &search_from_end('total time', \@logfileText);
  return "" if ($i == -1);

  $_ = $logfileText[$i];
  chomp;
  my @line_split = split(/\s+/,$_);
  $cpu_time = $line_split[4];
  return $cpu_time;
}

my $natom = 0;
my @symbols;

sub parse_psi_geometry
{
  local ($logfileName, *logfileText) = @_;

  my $outputXYZFileName = $logfileName;
  $outputXYZFileName =~ s/[^\/]+$/output\.xyz/;
  open(outputXYZ, ">$outputXYZFileName");

  my $i = &search_from_end('Center\s*X', \@logfileText);
  $i = $i + 2;
  $_ = $logfileText[$i];
  chomp;
  @words = split;
  while (scalar(@words) >= 4)
  {
   	my ($atnum, $x, $y, $z) = @words;
   	if ($atnum ne "Saving") {
   	print outputXYZ sprintf("%s %12f %12f %12f\n", $atnum, $x, $y, $z);
  	}
  	
	$natom++;
  	$_ = $logfileText[++$i];
  	@words = split;
  	chomp;
  }
  close(outputXYZ);

  my $connectionFileName = $outputXYZFileName;
  $connectionFileName =~ s/output\.xyz/connections/;
  # remake a connection file if required
  &silent_system("$perlPath build_connections.cgi \"$outputXYZFileName\" \"$connectionFileName\" silent") unless (-e $connectionFileName);
}

sub parse_psi_geometry_sequence
{
  local ($outputProperties, $logfileName, *logfileText) = @_;
  local $outputXYZFileName = $logfileName;
  $outputXYZFileName =~ s/[^\/]+$/output\.xyz_all/;

  my $sequence_energies;
  return if (search_from_beginning('Optimization Summary', \@logfileText) == -1);

  my $limitline = search_from_beginning('Optimization is complete!', \@logfileText);
  $_ = $logfileText[$limitline];
  my ($a,$b,$c,$d,$e,$numsteps,$f,$g) = split;
  $numsteps++;

  open(outputXYZ, ">$outputXYZFileName");
  my $frame = 1;
  $i = 0;
  while ($frame != $numsteps && ($i = search_forward('Justin Turney, Rob Parrish, and Andy Simmonett', $i, \@logfileText)) != -1)
  {
	my $ienergy = search_forward('Current energy   :', $i, \@logfileText);
	$_ = $logfileText[$ienergy];

	my ($a,$b,$c,$energy) = split;
	$sequence_energies .= "$frame,$energy:";
	$i = search_forward('Center', $i, \@logfileText);
	$i = $i + 2;
	$_ = $logfileText[$i];
	chomp;
	print outputXYZ "!Step: $frame (E=$energy)\n";
	@words = split;
	while (scalar(@words) >= 4)
	{
	 	my ($atnum, $x, $y, $z) = @words;
	 	if ($atnum ne "Saving") {
         	print outputXYZ sprintf("%s %12f %12f %12f\n", $atnum, $x, $y, $z);
        	}

        	$_ = $logfileText[++$i];
        	@words = split;
        	chomp;
	}
	$frame++;
	print outputXYZ "\n";
  }
  close(outputXYZ);
  print $outputProperties "Geometry Sequence=true\n";
  chop $sequence_energies;
  print $outputProperties "Geometry Sequence Energies=$sequence_energies\n";

}

sub parse_psi_symmetry
{
  local ($outputProperties, *logfileText) = @_;

  my $i = search_from_beginning('Molecular point group', \@logfileText);
  return if ($i == -1);

  $_ = $logfileText[$i];
  chomp;
  /Molecular point group:\s+(\S+)/;
  print $outputProperties "Symmetry=$1\n";
}

sub parse_psi_partial_charges
{
	local ($outputProperties, *logfileText) = @_;
	my $partial_charges = "";

	my $i = search_from_end('Mulliken Charges', \@logfileText);
	return if ($i == -1);

	$i+=2;
	$_ = $logfileText[$i];
	chomp;
	my @words = split;
	while(scalar(@words) == 6) {
		$partial_charges .= "$words[0],$words[1],$words[5]:";
		$_ = $logfileText[++$i];
		chomp;
		@words = split;
  	}
	chop $partial_charges;

	print $outputProperties "Partial Charges=$partial_charges\n";
}

sub parse_psi_dipole_moment
{
	local ($outputProperties, *logfileText) = @_;
	$x = search_from_end('CURRENT DIPOLE X', \@logfileText);
  $y = search_from_end('CURRENT DIPOLE Y', \@logfileText);
  $z = search_from_end('CURRENT DIPOLE Z', \@logfileText);
  
  $_ = $logfileText[$x];
	chomp;
	my @words = split;
	$x = @words[-1]*-1;

  $_ = $logfileText[$y];
	chomp;
	my @words = split;
	$y = @words[-1]*-1;
  
  $_ = $logfileText[$z];
	chomp;
	my @words = split;
	$z = @words[-1]*-1;
	
  $total = sqrt($x*$x+$y*$y+$z*$z);

	print $outputProperties "Dipole Moment=$x:$y:$z:$total Debye\n";
	return;
}


sub parse_psi_energy
{
	local ($outputProperties, *logfileText) = @_;
	$energy_found = 0;

	$i = search_from_end('"SCF TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "SCF Energy=$words[-1] Hartree\n";
		$energy_found = 1;
	}
	$i = search_from_end('"MP2 TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "MP2 Energy=$words[-1] Hartree\n";
		$energy_found = 1;
	}
	$i = search_from_end('"MP4 TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "MP4 Energy=$words[-1] Hartree\n";
		$energy_found = 1;
	}
	$i = search_from_end('"CCSD TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "CCSD Energy=$words[-1] Hartree\n";
		$energy_found = 1;
	}
	$i = search_from_end('"CCSD\(T\) TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "CCSD(T) Energy=$words[-1] Hartree\n";
		$energy_found = 1;
	}
	$i = search_from_end('"SAPT DISP ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Dispersion Energy=$words[-1] kcal/mol \n";
		$energy_found = 1;
	}
	$i = search_from_end('"SAPT ELST ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Electrostatics Energy=$words[-1] kcal/mol \n";
		$energy_found = 1;
	}
	$i = search_from_end('"SAPT EXCH ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Exchange Energy=$words[-1] kcal/mol \n";
		$energy_found = 1;
	}
	$i = search_from_end('"SAPT IND ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Induction Energy=$words[-1] kcal/mol \n";
		$energy_found = 1;
	}
	$i = search_from_end('"SAPT TOTAL ENERGY"', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Total Interaction Energy=$words[-1] kcal/mol \n";
		$energy_found = 1;
	}
	if ($energy_found == 0) {
		$i = search_from_end('"CURRENT ENERGY"', \@logfileText);
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		@words[-1] = @words[-1] * 627.5095;
		print outputProperties "Current Energy=$words[-1] kcal/mol \n";
	}
}

sub parse_psi_vibrational_modes
{
	local ($outputProperties, *logfileText) = @_;
	local @symmetries;
	local @frequencies;

	$i = search_from_beginning('Harmonic Frequency', \@logfileText);
	if($i == -1) {
		return;
  }
  $i+=3;

  $_ = @logfileText[$i];
  chomp;
  @words = split;
  while(scalar(@words) == 2) {
	push(@symmetries, $words[0]);
	push(@frequencies, $words[1]);

	$_ = @logfileText[++$i];
	chomp;
	@words = split;
  }
  
  $i += 9;
  $j = 0;
  

  while($j < scalar(@symmetries)) {
	$_ = @logfileText[$i];
	chomp;
	@words = split;
	$k = 1;
	while(scalar(@words) == 5) {
	  if($k == 1) {
		print $outputProperties "Mode".($j+1)."=$k,$words[1],$words[2],$words[3]";
	  }
	  else {
		print $outputProperties ":$k,$words[1],$words[2],$words[3]";
	  }
	  $k++;
	  $_ = @logfileText[++$i];
	  chomp;
	  @words = split;
	}
	print $outputProperties "\n";
	$j++;
	$i+=4;
  }
  
  $j = 1;
  while($j < scalar(@symmetries)+1) {
	if($j == 1) {
	  print $outputProperties "Vibrational Modes(v2)=$j,$symmetries[$j-1],$frequencies[$j-1],0";
	}
	else {
	  print $outputProperties ":$j,$symmetries[$j-1],$frequencies[$j-1],0";
	}
	$j++;
  }
  print $outputProperties "\n";

  return;
}

sub parse_psi_orbitals
{
	local ($outputProperties, $logfileName, *logfileText) = @_;
	&parse_molden($outputProperties, $logfileName, \@logfileText, $natom, 1);
}

sub parse_psi_force
{
  local ($outputProperties, *logfileText) = @_;
  
  $i = search_from_end('Geometry and Gradient', \@logfileText);
  return if ($i == -1);

  $rms = 0.0;
  $i += 1;
  $atoms = 1;
  $_ = $logfileText[$i]; chomp;
  @words = split;
  while(scalar(@words) == 4) {
	$i += 1;
	$atoms += 1;
	$_ = $logfileText[$i]; chomp;
	@words = split;
  }

  $rms += $words[0]*$words[0] + $words[1]*$words[1] + $words[2]*$words[2];
  $data = "1,$words[0],$words[1],$words[2]:";
  for(my $iatom = 2; $iatom < $atoms; $iatom++) {
	$_ = $logfileText[++$i]; chomp;
	my ($fx, $fy, $fz) = split;
	$rms += $fx*$fx+$fy*$fy+$fz*$fz;
	$data .= "$iatom,$fx,$fy,$fz:";
  }
  chop $data;
  $rms /= ($atoms*3);
  $rms = sprintf("%7.4f", sqrt($rms));
  
  print $outputProperties "Force=$data\n";
  print $outputProperties "RMS Force=$rms eV/A\n";
}

sub parse_psi_scan
{
  local ($outputProperties, $logfileName, *logfileText) = @_;
  my $outputXYZFileName = $logfileName;
  $outputXYZFileName =~ s/[^\/]+$/output\.xyz_all/;

  my $i = search_from_beginning("Values", \@logfileText);
  return if ($i == -1);

  my $scan_2d = 0;
  my $i2 = search_from_end("Values", \@logfileText)+1;
  $_ = $logfileText[$i2];
  @words = split;
  if(@words == 3) {
    $scan_2d = 1;
  }
  

  my @energies;
  my (@coordinates1, @coordinates2);
  my @points;

  if (!$scan_2d)
  {
    open(outputXYZ, ">$outputXYZFileName");
    my $i = search_from_end("Values", \@logfileText)+1;
    my $frame = 0;
    $_ = $logfileText[$i++];
    @words = split;
    while(@words == 2)
    {
      my $coordinate = $words[0];
      my $energy = $words[1];
      push(@coordinates1, $coordinate);
      push(@energies, $energy);
      $_ = $logfileText[$i++];
      chomp;
      @words = split;
    }

    my $geom_i = search_from_beginning("Center", \@logfileText);
    $geom_i += 2;
    $_ = $logfileText[$geom_i];
    chomp;
    while($geom_i < @logfileText && $geom_i != 1) {
      print outputXYZ "!Coordinate: $coordinates[$frame]  Energy: $energies[$frame]\n";
      @words = split;
      while(@words == 4) {
        my $symbol = $words[0];
        my $x = $words[1];
        my $y = $words[2];
        my $z = $words[3];
        print outputXYZ sprintf("$symbol %12f %12f %12f\n", $x, $y, $z);
        $_ = $logfileText[++$geom_i];
        chomp;
        @words = split;
      }
      print outputXYZ "\n";
      $geom_i = search_forward("Center", $geom_i, \@logfileText)+2;
      $_ = $logfileText[$geom_i];
      $frame++;
    }
    return if (@energies == 0);
  }
  else
  {
    my $i = search_from_end("Values", \@logfileText)+1;
    $_ = $logfileText[$i++];
    chomp;
    @words = split;
    while(@words == 3)
    {
      my $coordinate1 = $words[0];
      my $coordinate2 = $words[1];
      my $energy = $words[2];
      push(@coordinates1, $coordinate1);
      push(@coordinates2, $coordinate2);
      push(@energies, $energy);
      $_ = $logfileText[$i++];
      chomp;
      @words = split;
    }
    return if (@energies == 0);
  }

  for ($i = 0; $i < @energies; $i++)
  {
    if(!$scan_2d) {
      $points[$i] = "$coordinates1[$i],$energies[$i]";
      }
    else {
      $points[$i] = "$coordinates1[$i],$coordinates2[$i],$energies[$i]";
    }
  }

  close(outputXYZ);

  if(!$scan_2d) {
    print $outputProperties "Coordinate Scan(1D)=".join(":", @points)."\n";
  }
  else {
    print $outputProperties "Coordinate Scan(2D)=".join(":", @points)."\n";
  }

}

1;
