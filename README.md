# hadashboard
docker build timovp/hadashboard -t timovp/hadashboard:latest

docker push timovp/hadashboard:latest

arguments: -p 8050:8050 -v /mnt/user/appdata/HomeAssistantCore:/dbfolder