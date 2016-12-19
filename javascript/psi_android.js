function SubmitJob(form,preview)
{
	moledit.setModelFromBuilder();

        if (form.cartesianCoordinates.checked) getGeometry("XYZFormat", "", form.geometry, false);
        else getGeometry("PSI4Format", "writeEqualsSign=true", form.geometry, false);

	var response =JSON.parse(moledit.getProperties());
	document.form.dimScanned.value = response.dimScanned;
	document.form.scanVar.value = response.varScanned;
	document.form.scanStart.value = response.scanStart;
	document.form.scanStop.value = response.scanStop;
	document.form.scanSteps.value = response.scanSteps;
	document.form.scanVar2.value = response.varScanned2;
	document.form.scanStart2.value = response.scanStart2;
	document.form.scanStop2.value = response.scanStop2;
	document.form.scanSteps2.value = response.scanSteps2;
	
	getGeometry("XYZFormat", "writeUnitCell=true", form.cartesian, false);
	getGeometry("ConnectionFormat", "", form.connections, false);
	getGeometry("ZMatrixFormat", "", form.zmatrix, false);
	getGeometry("ChargeFormat", "", form.charges, false);
	
	DoSubmitJob(form, preview);		
}
		
