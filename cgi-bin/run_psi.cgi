#!/usr/bin/perl

my ($jobNumber, $jobOwner, $queue) = @ARGV;

$require++;
require("globals.cgi");
require("run_parallel.cgi");
&load_interface("interfaces/psi.int");
&load_interface("queues/$queue/psi.int") if ($externalBatchQueue);
$require--;

my $input_directory = "$userBase/$jobOwner/$jobNumber";
my ($input_file, $output_file)  = ("$input_directory/input.dat", "$input_directory/output.out");

print "Executing script: $0\n";
	
my $jobScratch = "$systemScratch/webmo-$uniqueId/$jobNumber";
print "Creating working directory: $jobScratch\n";
unless (-e $jobScratch) {
	mkdir($jobScratch, 0755) || die "Cannot create directory $jobScratch: $!";
}

$ENV{'HOME'}=$jobScratch;
#PSI must be FIRST in path -- otherwise we will likely run the wrong (system) Perl version
$ENV{'PATH'} = "$psiBase/bin:" . $ENV{'PATH'};

# if we are using PBS, find out which host we are running on
if ($externalBatchQueue)
{
	$host = `hostname`;
	chomp $host;
}
print "Script execution node: $host\n";

#parallel job support
my (@node_list, @unique_nodes, %ppn, $nnode, $nproc, $node_file);
&get_nodefile_info($input_directory,\@node_list, \@unique_nodes, \%ppn, \$nnode, \$nproc, \$node_file);
print "Job execution node(s): ", join(' ', @node_list), "\n";

if($psi_pid = fork)
{
	open(pid, ">$input_directory/pid");
	print pid $psi_pid;
	close(pid);
	
}
elsif($nproc > 1)
{
  $SIG{'INT'} = 'DEFAULT';
  $SIG{'TERM'} = 'DEFAULT';

  # change directory to the job directory for some output files
  chdir($input_directory);

  my $exec_command = "$psiBase/bin/psi4 -p $jobNumber -s $jobScratch input.inp output.out -n $nproc";
  print "Executing command: $exec_command\n";

  open(STDIN, "<$input_file");
  open(STDOUT, ">$output_file.stdout");
  open(STDERR, ">$output_file.stderr");
  exec($exec_command);
  print STDERR "Cannot execute $psiBase/bin/psi4: $!";

  close(STDIN);
  close(STDOUT);
  close(STDERR);
  exit(0);
}
else
{
	$SIG{'INT'} = 'DEFAULT';
	$SIG{'TERM'} = 'DEFAULT';
	
	# change directory to the job directory for some output files
	chdir($input_directory);
	
	my $exec_command = "$psiBase/bin/psi4 -p $jobNumber -s $jobScratch input.inp output.out";
	print "Executing command: $exec_command\n";

	open(STDIN, "<$input_file");
	open(STDOUT, ">$output_file.stdout");
	open(STDERR, ">$output_file.stderr");
	exec($exec_command);
	print STDERR "Cannot execute $psiBase/bin/psi4: $!";
		
	close(STDIN);
	close(STDOUT);
	close(STDERR);
	exit(0);
}
waitpid($psi_pid, 0);

# Append any text from STDOUT and STDERR to the output file
system("$catPath $output_file.stdout $output_file.stderr >> $output_file");
unlink("$output_file.stdout");
unlink("$output_file.stderr");
