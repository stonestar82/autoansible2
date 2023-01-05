import yaml, json
from generators.generateInventory import generateInventory 
from jinja2 import Template
from generators.BlankNone import BlankNone
from operator import eq
from generators.BlankNone import *
from openpyxl import load_workbook

def taskPrint(task):
	task = task + " "
	print(task.ljust(100, "*") + "\n")

def main():
    
	taskPrint("TASK [Start]")	

	## 엑셀파일 지정
	file_location = "./inventory.xlsx"
	
	with open("./excelEnvriment.json", "r") as f:
		excelVar = json.load(f)
		f.close()

	workbook = load_workbook(filename=file_location, read_only=False, data_only=True)
	fabric_name = getExcelSheetValue(workbook, excelVar["all"]["fabricName"])
 
	avd = {
		"inventory": None,
		"group_vars": {
			fabric_name: None
			}
	}

	taskPrint("TASK [inventory Parsing]")
	## 엑셀에서 데이터를 읽어 inventory 정보 처리 d1.yml, all.yml 파일 생성
	avd["inventory"] = generateInventory(file_location, excelVar)

	## Create inventory file
	## yaml.dump시 sort_keys=False 값을 주지 않으면 키값 기준으로 오름차순으로 정렬되어 적용됨
	## sort_keys=False 실제 적용한 값 순서대로 처리
	taskPrint("TASK [inventory.yml Generate]")
	with BlankNone(), open("./inventory/inventory.yml", "w") as inv:
			inv.write(yaml.dump(avd["inventory"], sort_keys=False))


	## config, deploy playbook 생성
	taskPrint("TASK [deploy.yml PlayBook Generate]")

	sessionList = ["Full", "Init", "Base", "Loop0", "P2Pip", "BGPv4", "P2Pipv6", "BGPv6", "ETCPort", "VXLAN"]
	data = { 
					"fabricName" : fabric_name, 
					"setFacsSwitch": "{{ hostvars[inventory_hostname]['hosts'][inventory_hostname] }}",
					"configTempateSrc": "{{ config_template_dir }}",
					"configGenDest": "{{ config_gen_dir }}/{{ inventory_hostname }}",
					"backupFileName": "{{ inventory_hostname }}_{{ lookup('pipe', 'date +%Y%m%d%H%M%S') }}",
					"runningConfigBackup": "{{ eos_config_deploy_eapi_pre_running_config_backup }}",
					"runningConfigBackupFileName": "{{ pre_running_config_backup_filename }}",
					"runningConfigBackupDir": "{{ pre_running_config_backup_dir }}",
					"inventoryHostname": "{{ inventory_hostname }}",
					"replaceType": "line",
					"session": ""
					}

	## deploy 생성용 jinja2
	with open('./inventory/templates/playbook/deploy.j2', encoding='utf8') as f:
		deployTemplate = Template(f.read())
		f.close()	

	## config 생성용 jinja2
	with open('./inventory/templates/playbook/config.j2', encoding='utf8') as f:
		configTemplate = Template(f.read())
		f.close()
  
  ## 정의해놓은 단계별로 각각의 config.yml, deploy.yml 생성
	for session in sessionList:
		
		## init, full 단계는 적용이 config 모드로 적용됨
		## replaceType : config = 기존 running-config 삭제 새로운 config로 적용
		## replaceType : line = 기존 running-config 수정하지 않고 추가로 등록됨
		if eq("Init", session) or eq("Full", session):
			data["replaceType"] = "config"
		else:
			data["replaceType"] = "line"
   
		data["session"] = str(session).lower()
   
		with open("./deploy" + session + ".yml", "w", encoding='utf8') as reqs:
			reqs.write(deployTemplate.render(**data))
			reqs.close()

		with open("./config" + session + ".yml", "w", encoding='utf8') as reqs:
				reqs.write(configTemplate.render(**data))
				reqs.close()


if __name__ == "__main__":
	main()