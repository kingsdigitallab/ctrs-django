wget "http://10.0.2.2:8001/digipal/api/annotation/?_type=text&_image__id__in=[4,5]&@select=id,geo_json,image_id&@limit=1000" -O media/arch-annotations.json
curl "http://10.0.2.2:8001/digipal/api/textcontentxml/?@select=*status,id,str,content,*text_content,*item_part,group,group_locus,type,*current_item,locus,shelfmark,*repository,place&@limit=10000" > arch-content.json
