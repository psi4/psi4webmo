function SubmitJob(form,preview) {
	document.moledit.setModel(form.model.value);
	var response = JSON.parse(document.moledit.getProperties());
		
	document.form.dimScanned.value = response.dimScanned;
	document.form.scanVar.value = response.varScanned;
	document.form.scanStart.value = response.varScanned2;
	document.form.scanStop.value = response.scanStop;
	document.form.scanSteps.value = response.scanSteps;
	document.form.scanVar2.value = response.dimScanned;
	document.form.scanStart2.value = response.scanStart2;
	document.form.scanStop2.value = response.scanStop2;
	document.form.scanSteps2.value = response.scanSteps2;
	
	if (form.cartesianCoordinates.checked)
		getGeometry("XYZFormat", "", form.geometry, false);
	else
		getGeometry("PSI4Format", "writeEqualsSign=true", form.geometry, false);
	
	getGeometry("XYZFormat", "writeUnitCell=true", form.cartesian, false);
	getGeometry("ConnectionFormat", "", form.connections, false);
	getGeometry("ZMatrixFormat", "", form.zmatrix, false);
	getGeometry("ChargeFormat", "", form.charges, false);
	
	DoSubmitJob(form, preview);		
}

function OnChangeTemplateId(form)
{
	var temp = form.templateId.options[form.templateId.selectedIndex].text;
	if (temp == "SAPT") {
		form.functional.selectedIndex = 0;
		form.functional.disabled=true;
		form.method.selectedIndex = 6;
		form.basisSet.selectedIndex = 4;
	}
	if (temp.substring(0, 5) == "Other")
	{
		var text = window.prompt("Enter calculation", "SP");

		form.calculation.value = text;
		form.templateId.options[form.templateId.selectedIndex].text = "Other (" + text + ")";
	}
	hideUnusedVariables();
}

function OnChangeMethod(form)
{
	var method = form.method.options[form.method.selectedIndex].value;
	if (method == 'dft')
	{
		form.functional.disabled=false;
		form.basisSet.selectedIndex = 0;
		
	} else if (method == 'sapt0' || method == 'sapt2' || method == 'sapt2+(3)' || method == 'sapt2+(3)dmp2') {
		form.functional.selectedIndex = 0;
		form.functional.disabled=true;
		form.basisSet.selectedIndex = 4;
	} else { 	
		form.functional.selectedIndex = 0;
		form.functional.disabled=true;
		form.basisSet.selectedIndex = 0;
	}

}

function OnChangeFunctional(form)
{
}

function OnChangeBasis(form)
{
	if (form.basisSet.selectedIndex == form.basisSet.length - 1)
	{
		var text = window.prompt("Enter Basis", "3-21G");

		form.basisSet.options[form.basisSet.selectedIndex].value = text;
		form.basisSet.options[form.basisSet.selectedIndex].text = "Other (" + text + ")";
	}
}

function OnChangeMultiplicity(form)
{
}

function OnChangeReference(form)
{
	var ref = form.reference.options[form.reference.selectedIndex].value;
	if (ref == "rhf") {
		form.multiplicity.disabled = true;
		form.multiplicity.selectedIndex = 0;
	}
	else {
		form.multiplicity.disabled = false;
	}
}

