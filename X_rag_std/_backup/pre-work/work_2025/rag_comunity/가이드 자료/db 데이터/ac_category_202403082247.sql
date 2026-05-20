INSERT INTO ac.ac_category (company_id,project_id,category_name,parent_category_name,category_level,leaf_level_yn,order_sn,create_id,create_dt,modify_id,modify_dt) VALUES
	 ('item','2','AICC',NULL,1,'Y',3,'admin','2023-11-23 00:00:00',NULL,NULL),
	 ('item','10','1단계카테고리','',1,'N',1,'admin','2023-12-21 10:55:08',NULL,NULL),
	 ('item','10','2단계카테고리','1단계카테고리',2,'N',1,'admin','2023-12-21 10:55:46',NULL,NULL),
	 ('item','10','3단계카테고리-22222','2단계카테고리',3,'Y',1,'admin','2023-12-21 10:56:05',NULL,NULL),
	 ('item35','35','1단계','',1,'Y',NULL,'admin','2024-01-10 00:00:00',NULL,NULL);
