#!/usr/bin/perl

$require++;
require("parse_output.cgi");
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

  ($version) = $_ =~ m/PSI\d* (.*) Driver/i;
  return $version;

}

sub parse_psi_normal_termination
{
  local (*logfileText) = @_;
  return &search_from_end('PSI4 exiting successfully', \@logfileText) != -1;
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

  $i = search_from_beginning('Number of atoms', \@logfileText);
  ($natom) = /(\d+)/;
  
  return unless ($natom > 0);
  
  my $outputXYZFileName = $logfileName;
  $outputXYZFileName =~ s/[^\/]+$/output\.xyz/;
  open(outputXYZ, ">$outputXYZFileName");
  
  $i = search_from_end('Cartesian Geometry', \@logfileText);
  if (($i != -1))
  {
	$i += 1;
	$_ = $logfileText[$i];
	chomp;  # Delete trailing spaces and newlines
	s/^\s+\(\s+//;   #Delete leading spaces and parenthesis
	
	@words = split;
	for (my $iatom = 0; $iatom < $natom; $iatom++)
	{
	  my ($atnum, $x, $y, $z) = @words;
    @letters = split('',$atnum);
    @letters[1] = lc(@letters[1]);
    $atnum = join('',@letters);
	  print outputXYZ sprintf("%s %12f %12f %12f\n", $atnum, $x, $y, $z);

	  $_ = $logfileText[++$i];
	  chomp;  # Delete trailing spaces and newlines
	  s/^\s+\(\s+//;   #Delete leading spaces and parenthesis
	  @words = split;
	}
	close(outputXYZ);
  }
  else
  {
	$i = search_from_beginning('Center', \@logfileText);
	$i += 2;
	$_ = $logfileText[$i];
	chomp;
	s/^\s+//;

	for (my $iatom = 0; $iatom < $natom; $iatom++)
	{
	  @words = split;
	  my ($atnum, $x, $y, $z) = @words;
    @letters = split('',$atnum);
    @letters[1] = lc(@letters[1]);
    $atnum = join('',@letters);
	  $x = $x;
	  $y = $y;
	  $z = $z;
	  print outputXYZ sprintf("%s %12f %12f %12f\n", $atnum, $x, $y, $z);

	  $_ = $logfileText[++$i];
	  chomp;
	  s/^\s+//;
	}
	close(outputXYZ);
  }

  my $connectionFileName = $outputXYZFileName;
  $connectionFileName =~ s/output\.xyz/connections/;
# remake a connection file if required
  system("$cgiBase/build_connections.cgi $outputXYZFileName $connectionFileName silent");
}

sub parse_psi_geometry_sequence
{
  local ($outputProperties, $logfileName, *logfileText) = @_;
  local $outputXYZFileName = $logfileName;
  $outputXYZFileName =~ s/[^\/]+$/output\.xyz_all/;

  my $sequence_energies;
  return if (search_from_beginning('Optimization Summary', \@logfileText) == -1);

  open(outputXYZ, ">$outputXYZFileName");
  my $frame = 1;
  $i = 0;
  while (($i = search_forward('Structure for next step', $i, \@logfileText)) != -1)
  {
	my $ienergy = search_backward('Current energy   :', $i, \@logfileText);
	$_ = $logfileText[$ienergy];

	my ($a,$b,$c,$energy) = split;
	$sequence_energies .= "$frame,$energy:";
	$i = search_forward('Cartesian Geometry', $i, \@logfileText);
	$_ = $logfileText[++$i];
	chomp;
	print outputXYZ "!Step: $frame (E=$energy)\n";
	@words = split;
	while (scalar(@words) == 4)
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
	$x = search_from_end('SCF DIPOLE X', \@logfileText);
  $y = search_from_end('SCF DIPOLE Y', \@logfileText);
  $z = search_from_end('SCF DIPOLE Z', \@logfileText);
  
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

	$i = search_from_end('SCF TOTAL ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "SCF Energy=$words[-1] Hartree\n";
    $energy_found = 1;
	}
	$i = search_from_end('MP2 TOTAL ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "MP2 Energy=$words[-1] Hartree\n";
    $energy_found = 1;
	}
	$i = search_from_end('MP4 TOTAL ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "MP4 Energy=$words[-1] Hartree\n";
    $energy_found = 1;
	}
	$i = search_from_end('CCSD TOTAL ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "CCSD Energy=$words[-1] Hartree\n";
    $energy_found = 1;
	}
	$i = search_from_end('CCSD\(T\) TOTAL ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
		print outputProperties "CCSD(T) Energy=$words[-1] Hartree\n";
    $energy_found = 1;
	}
	$i = search_from_end('SAPT DISP ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
    @words[-1] = @words[-1] * 627.5095;
		print outputProperties "Dispersion Energy=$words[-1] kcal/mol \n";
    $energy_found = 1;
	}
	$i = search_from_end('SAPT ELST ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
    @words[-1] = @words[-1] * 627.5095;
		print outputProperties "Electrostatics Energy=$words[-1] kcal/mol \n";
    $energy_found = 1;
	}
	$i = search_from_end('SAPT EXCH ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
    @words[-1] = @words[-1] * 627.5095;
		print outputProperties "Exchange Energy=$words[-1] kcal/mol \n";
    $energy_found = 1;
	}
	$i = search_from_end('SAPT IND ENERGY', \@logfileText);
	if ($i != -1) {
		$_ = $logfileText[$i];
		chomp;
		my @words = split;
    @words[-1] = @words[-1] * 627.5095;
		print outputProperties "Induction Energy=$words[-1] kcal/mol \n";
    $energy_found = 1;
	}
  if ($energy_found == 0) {
    $i = search_from_end('CURRENT ENERGY', \@logfileText);
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
	
	(my $moldenFileName = $logfileName) =~ s/[^\/]+$/output\.molden/;
	return if (!-e $moldenFileName);
	open(moldenFile,"<$moldenFileName");
	my @moldenContents = <moldenFile>;
	close(moldenFile);
	
	(my $basisFileName = $logfileName) =~ s/[^\/]+$/output\.basis/;
	open(basisFile, ">$basisFileName");
	
	# write out atoms
	(my $xyzFileName = $logfileName) =~ s/[^\/]+$/output\.xyz/;
	open(xyzFile, "<$xyzFileName");
	print basisFile "[ATOMS]\n";
	while (<xyzFile>)
	{
		chomp;
		local ($atomicNumber, $x, $y, $z) = split;
		$x /= $bohrRadius; # convert to bohr (thats what all the coefficients are in)
		$y /= $bohrRadius;
		$z /= $bohrRadius;
		print basisFile "$atomicNumber $x $y $z\n";
	}
	print basisFile "\n";
	close(xyzFile);
	
	#write out bonds
	(my $connectionsFileName = $logfileName) =~ s/[^\/]+$/connections/;
	open(connectionsFile, "<$connectionsFileName");
	print basisFile "[BONDS]\n";
	print basisFile <connectionsFile>;
	print basisFile "\n";
	close(connectionsFile);

	#write out basis
	my $spherical_d = search_from_beginning('\[5d\]|\[5D\]', \@moldenContents) != -1 ? 1 : 0;
	#accordingly to the Molden manual, 5d also implies 7f
	my $spherical_f = search_from_beginning('\[5d\]|\[5D\]', \@moldenContents) != -1 ? 1 : 0;
	
	print basisFile "[AO_ORDER]\n";
	print basisFile "DOrbitals XX YY ZZ XY XZ YZ\n";
	print basisFile "FOrbitals XXX YYY ZZZ YYX XXY XXZ ZZX ZZY YYZ XYZ\n";
	print basisFile "Y2m 0 1 -1 2 -2\n";
	print basisFile "Y3m 0 1 -1 2 -2 3 -3\n\n";	
	print basisFile "[GTO]\n";
	my $i = search_from_beginning('\[GTO\]', \@moldenContents);
	$i++;
	my $nao;
	for (my $atom = 1; $atom <= $natom; $atom++)
	{
		$_ = $moldenContents[$i++]; chomp;
		my ($center, $dum) = split;
		$_ = $moldenContents[$i]; chomp;
		
		while(!/^\s*$/)
		{
			$_ = $moldenContents[$i++]; chomp;
			my ($type, $numPrimatives) = split;
			$type =~ tr/a-z/A-Z/;
			$type = "D6" if ($type eq "D" && !$spherical_d);
			$type = "D5" if ($type eq "D" && $spherical_d);
			$type = "F10" if ($type eq "F" && !$spherical_f);
			$type = "F7" if ($type eq "F" && $spherical_f);
			
			$nao += 1 if ($type eq "S");
			$nao += 3 if ($type eq "P");
			$nao += 4 if ($type eq "SP");
			$nao += 5 if ($type eq "D5");
			$nao += 6 if ($type eq "D6");
			$nao += 7 if ($type eq "F7");
			$nao += 10 if ($type eq "F10");

			print basisFile "$center\n";
			print basisFile "$type $numPrimatives\n";
			for (my $prim = 1; $prim <= $numPrimatives; $prim++)
			{
				$_ = $moldenContents[$i++]; chomp;
				my ($exponent, $coeff) = split;
				foreach ($exponent, $coeff) { tr/D/e/; $_ *= 1.0; }
				
				print basisFile "$exponent $coeff\n";
			}
			print basisFile "\n";
			
			$_ = $moldenContents[$i];
		}
		
		$i++;
	}
	close(basisFile);
	
	#write out MOs
	$i = search_from_beginning('\[MO\]', \@moldenContents);
	
	my $norbital;
	my @mo_occupancy;
	my @mo_energies;
	my @mo_coefficients;
	
	while ( ($i = search_forward('Ene=', $i, \@moldenContents)) != -1)
	{
			$_ = $moldenContents[$i++]; chomp;
			push(@mo_energies, (split)[1]);
			$i = search_forward('Occup=', $i, \@moldenContents);
			$_ = $moldenContents[$i++]; chomp;
			push(@mo_occupancy, int((split)[1]));
			
			$_ = $moldenContents[$i];
			my @orbital;
			while (!/Ene=/ && !/^\s*$/ && $i < @moldenContents)
			{
				chomp;
				my ($index, $coefficient) = split;
		push(@orbital, $coefficient);
				$_ = $moldenContents[++$i];
			}
			push(@mo_coefficients, \@orbital);
			$norbital++;
	}
		
	(my $moFileName = $logfileName) =~ s/[^\/]+$/output.mo/;
	open(moFile, ">$moFileName");
	for ($i = 0; $i < $norbital; $i++)
	{		
		my $mo_index = $i + 1;
		print moFile "[MO${mo_index}]\n";
		print moFile $mo_energies[$i]."\n";
		print moFile $mo_occupancy[$i]."\n";
		
		my ($orbital, $coefficient_list) = ($mo_coefficients[$i], "");
		for (my $j = 1; $j <= $nao; $j++) {
			$coefficient_list .= "$j   $orbital->[$j-1]\n";
		}
		print moFile $coefficient_list;
		print moFile "\n\n";
	}
	close(moFile);
	
	my $data;
	for ($i = 0; $i < $norbital; $i++)
	{
		my $mo_index = $i + 1;
		$data .= "$mo_index,-,$mo_occupancy[$i],$mo_energies[$i] Hartree:";
	}
	chop $data;
	print $outputProperties "Molecular Orbitals=$data\n";	
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
