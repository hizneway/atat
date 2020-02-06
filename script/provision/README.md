This folder contains a series of scripts to do the parts of provisioning that do not have UIs.

You need to start by copying sample.json in this directory and filling in your real values.

Then you can run each script in turn, with the following:
```
pipenv run ./script/provisiong/name_of_script.py input.json output.json
```
Note: Run this script from the root of the project, the paths to your json files need to be relative to where you're running the command from

You should see output detailing each thing the script is doing, or error details if it fails. Once the script is done, it writes all the input (from the input.json) updated with new values from the script.

These are meant to be run in sequence, consuming the output of the previous script:
```
pipenv run ./script/provisiong/a_create_tenant.py input.json tenant_output.json
pipenv run ./script/provisiong/b_setup_billing.py tenant_output.json billing_output.json
pipenv run ./script/provisiong/c_billing_profile_tenant_access.py billing_output.json ta_output.json
pipenv run ./script/provisiong/d_setup_to_billing.py ta_output.json to_billing_output.json
pipenv run ./script/provisiong/e_report_clin.py to_billing_output.json clin_report_output.json
pipenv run ./script/provisiong/f_purchase_aadp.py clin_report_output.json purchase_output.json
```

If there were no errors, running the above with a valid input.json would be a complete process.
