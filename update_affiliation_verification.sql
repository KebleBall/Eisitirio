UPDATE `user` SET `affiliation_verified`=1 WHERE `user`.`college_id` IN (12, 27) AND `user`.`affiliation_id` = 1 AND `user`.`battels_id` IS NOT NULL
