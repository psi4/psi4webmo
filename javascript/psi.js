		function SubmitJob(form,preview)
		{
			document.TranslatorApplet.setModel(form.model.value);
			if (form.cartesianCoordinates.checked)
				form.geometry.value = document.TranslatorApplet.getGeometry("XYZFormat");
			else
				form.geometry.value = document.TranslatorApplet.getGeometry("PSI4Format", "writeEqualsSign=true");
			form.cartesian.value = document.TranslatorApplet.getGeometry("XYZFormat");
			form.connections.value = document.TranslatorApplet.getGeometry("ConnectionFormat");
			form.zmatrix.value = document.TranslatorApplet.getGeometry("ZMatrixFormat");
			form.charges.value = document.TranslatorApplet.getGeometry("ChargeFormat");
			
			form.dimScanned.value = document.TranslatorApplet.dimScanned;
			form.scanVar.value = document.TranslatorApplet.varScanned;
			form.scanStart.value = document.TranslatorApplet.scanStart;
			form.scanStop.value = document.TranslatorApplet.scanStop;
			form.scanSteps.value = document.TranslatorApplet.scanSteps;
			form.scanVar2.value = document.TranslatorApplet.varScanned2;
			form.scanStart2.value = document.TranslatorApplet.scanStart2;
			form.scanStop2.value = document.TranslatorApplet.scanStop2;
			form.scanSteps2.value = document.TranslatorApplet.scanSteps2;
		
			DoSubmitJob(form,preview);				
		}
		
		function OnChangeTemplateId(form)
		{
			var temp = form.templateId.options[form.templateId.selectedIndex].text;
			if (temp == "SAPT") {
				form.functional.selectedIndex = 0;
				form.functional.disabled=true;
				form.method.selectedIndex = 7;
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
			}
			else {
				form.functional.selectedIndex = 0;
				form.functional.disabled=true;
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
		
