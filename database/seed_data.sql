INSERT INTO strengths (strength_id, name_zh, category, description, suggestion, fruit_name, outfit_reward) VALUES
('creativity', '創造力', '智慧及知識', '能想出新的方法、點子或作品，讓事情有不同的可能。', '今天可以試著用一個新方法完成小任務，或畫下你想到的新點子。', '創意果實', 'creativity_brush'),
('curiosity', '好奇心', '智慧及知識', '願意提問、探索，想知道事情為什麼會這樣。', '遇到不懂的事，可以先問一個「為什麼」或「怎麼做到」。', '好奇果實', 'curiosity_hat'),
('judgment', '判斷力', '智慧及知識', '能停下來想一想，從不同角度看事情再做決定。', '做決定前，可以試著列出兩個選項各自的好處和困難。', '判斷果實', 'judgment_lens'),
('love_of_learning', '喜愛學習', '智慧及知識', '喜歡理解新知識，也願意多練習讓自己更懂。', '挑一個今天想更懂的小知識，花五分鐘查一查或問問看。', '學習果實', 'learning_glasses'),
('perspective', '洞察力', '智慧及知識', '能把經驗整理成想法，也能給出有幫助的觀點。', '遇到一件事後，可以想想「我從這件事學到什麼」。', '洞察果實', 'perspective_map'),
('bravery', '勇敢', '勇氣', '就算有點害怕或緊張，仍願意面對重要的事情。', '今天可以選一件小小有點難的事，慢慢試一次。', '勇敢果實', 'bravery_cape'),
('perseverance', '勤奮', '勇氣', '遇到困難時仍願意練習、完成任務，讓自己一步一步進步。', '把一件困難任務切成很小的一步，先完成第一步就好。', '勤奮果實', 'perseverance_boots'),
('honesty', '真誠', '勇氣', '能誠實表達自己的想法、感受與狀態。', '可以試著用一句話說出你真正的感覺，例如「我其實有點擔心」。', '真誠果實', 'honesty_badge'),
('zest', '熱誠', '勇氣', '對喜歡的事有活力，也願意投入其中。', '找一件讓你有精神的小事，給自己十分鐘好好投入。', '熱誠果實', 'zest_scarf'),
('love', '愛與被愛', '仁愛', '重視親近的人，也願意接住彼此的關心。', '今天可以對一位重要的人說一句謝謝或關心的話。', '關愛果實', 'love_pin'),
('kindness', '仁慈', '仁愛', '願意關心、幫助或安慰別人。', '你可以試著今天對一位同學說一句鼓勵的話。', '仁慈果實', 'kindness_cloak'),
('social_intelligence', '社交智慧', '仁愛', '能察覺自己和別人的感受，並調整互動方式。', '聊天時可以觀察對方的表情，想想他現在可能需要什麼。', '社交果實', 'social_bridge_badge'),
('teamwork', '團體合作', '公義', '願意和大家一起完成任務，也會重視隊友。', '下次分組時，可以主動問一句「我可以負責哪一部分」。', '合作果實', 'teamwork_scarf'),
('fairness', '公平', '公義', '重視每個人都被合理對待，不只想到自己。', '遇到分配時，可以想想每個人的需要是否都有被看見。', '公平果實', 'fairness_scale'),
('leadership', '領導力', '公義', '能協助大家整理方向，帶著團隊往前。', '當大家不知道怎麼開始時，可以先提一個小步驟。', '領導果實', 'leadership_flag'),
('forgiveness', '寬恕', '節制', '願意慢慢放下受傷或不舒服，不一直困在責怪裡。', '如果還不能原諒也沒關係，可以先說出自己受傷的地方。', '寬恕果實', 'forgiveness_leaf'),
('humility', '謙遜', '節制', '知道自己的長處，也願意承認還有能學習的地方。', '完成一件事後，可以想想哪裡做得好、哪裡還能更好。', '謙遜果實', 'humility_patch'),
('prudence', '審慎', '節制', '行動前會想一想，避免讓自己或別人受傷。', '做重要決定前，可以先停三秒，想想可能的後果。', '審慎果實', 'prudence_lantern'),
('self_regulation', '自我規範', '節制', '能管理自己的情緒、注意力或行動，讓自己慢慢穩定。', '如果心情亂，可以先深呼吸三次，再決定下一步。', '規範果實', 'self_regulation_shield'),
('appreciation_of_beauty', '欣賞美好', '靈性及超越', '能注意生活裡美麗、特別或讓人感動的事物。', '今天可以找一個你覺得漂亮或有趣的小細節。', '美好果實', 'beauty_camera'),
('gratitude', '感激', '靈性及超越', '能看見別人的付出，並感受到謝意。', '今天可以向一個幫助你的人說謝謝。', '感激果實', 'gratitude_badge'),
('hope', '希望', '靈性及超越', '相信未來仍有可能，也願意朝目標前進。', '想一個你希望變好的地方，寫下一個今天能做的小步驟。', '希望果實', 'hope_compass'),
('humor', '幽默', '靈性及超越', '能用輕鬆有趣的方式看事情，讓氣氛變柔和。', '今天可以分享一件讓你微笑的小事。', '幽默果實', 'humor_button'),
('spirituality', '靈性', '靈性及超越', '能感覺自己和更大的意義、信念或價值有連結。', '可以想想一件對你很重要、讓你想努力的原因。', '靈性果實', 'spirit_star')
ON DUPLICATE KEY UPDATE
name_zh = VALUES(name_zh),
category = VALUES(category),
description = VALUES(description),
suggestion = VALUES(suggestion),
fruit_name = VALUES(fruit_name),
outfit_reward = VALUES(outfit_reward);

INSERT INTO outfits (outfit_id, name, display_name, related_strength_id, cost) VALUES
('starter_scarf', 'starter_scarf', '初心圍巾', NULL, 0),
('creativity_brush', 'creativity_brush', '創意畫筆', 'creativity', 20),
('curiosity_hat', 'curiosity_hat', '好奇帽', 'curiosity', 20),
('judgment_lens', 'judgment_lens', '判斷放大鏡', 'judgment', 20),
('learning_glasses', 'learning_glasses', '學習眼鏡', 'love_of_learning', 20),
('perspective_map', 'perspective_map', '洞察地圖', 'perspective', 20),
('bravery_cape', 'bravery_cape', '勇敢披風', 'bravery', 20),
('perseverance_boots', 'perseverance_boots', '勤奮靴', 'perseverance', 20),
('honesty_badge', 'honesty_badge', '真誠徽章', 'honesty', 20),
('zest_scarf', 'zest_scarf', '熱誠領巾', 'zest', 20),
('love_pin', 'love_pin', '關愛別針', 'love', 20),
('kindness_cloak', 'kindness_cloak', '仁慈斗篷', 'kindness', 20),
('social_bridge_badge', 'social_bridge_badge', '社交橋徽章', 'social_intelligence', 20),
('teamwork_scarf', 'teamwork_scarf', '合作圍巾', 'teamwork', 20),
('fairness_scale', 'fairness_scale', '公平天秤', 'fairness', 20),
('leadership_flag', 'leadership_flag', '領導小旗', 'leadership', 20),
('forgiveness_leaf', 'forgiveness_leaf', '寬恕葉片', 'forgiveness', 20),
('humility_patch', 'humility_patch', '謙遜布章', 'humility', 20),
('prudence_lantern', 'prudence_lantern', '審慎提燈', 'prudence', 20),
('self_regulation_shield', 'self_regulation_shield', '自我規範盾牌', 'self_regulation', 20),
('beauty_camera', 'beauty_camera', '美好相機', 'appreciation_of_beauty', 20),
('gratitude_badge', 'gratitude_badge', '感激徽章', 'gratitude', 20),
('hope_compass', 'hope_compass', '希望羅盤', 'hope', 20),
('humor_button', 'humor_button', '幽默鈕扣', 'humor', 20),
('spirit_star', 'spirit_star', '靈性星星', 'spirituality', 20)
ON DUPLICATE KEY UPDATE
display_name = VALUES(display_name),
related_strength_id = VALUES(related_strength_id),
cost = VALUES(cost);

INSERT INTO children (child_id, username, password_hash, name, tokens, selected_character, selected_outfit) VALUES
('child_B', 'studentB', '1234', 'B生', 100, 'fox', 'perseverance_boots'),
('child_C', 'studentC', '1234', 'C生', 100, 'cat', 'self_regulation_shield'),
('child_D', 'studentD', '1234', 'D生', 100, 'rabbit', 'hope_compass')
ON DUPLICATE KEY UPDATE
username = VALUES(username),
password_hash = VALUES(password_hash),
name = VALUES(name),
tokens = VALUES(tokens),
selected_character = VALUES(selected_character),
selected_outfit = VALUES(selected_outfit);

DELETE FROM child_strengths WHERE source = 'counseling_record';

INSERT INTO child_strengths (child_id, strength_id, source, evidence_text, confidence) VALUES
('child_B', 'perseverance', 'counseling_record', '面對數學、地理、歷史與英文口說等任務時，即使一開始不情願、概念不熟或需要反覆修改，仍願意完成指定進度並持續複習。', 0.950),
('child_B', 'self_regulation', 'counseling_record', '能在情緒起伏後逐漸穩定下來，也能在複習時控制自己專心看書，並嘗試主動安排想學或需要加強的內容。', 0.950),
('child_B', 'social_intelligence', 'counseling_record', '會主動與老師和同儕分享生活事件，也嘗試透過共同興趣與同學建立關係，並能較清楚表達自己在人際互動中的感受。', 0.950),
('child_B', 'love_of_learning', 'counseling_record', '在複習地理、國文訂正與數學練習時，會主動做筆記、翻課本找答案，或多寫題目來確認自己是否理解。', 0.950),
('child_B', 'honesty', 'counseling_record', '能直接表達自己被忽略的感受，也會坦率承認錯題是因為沒有認真看題目，展現對自身狀態的真實覺察。', 0.950),
('child_C', 'self_regulation', 'counseling_record', '能準時進教室拿出作業、主動開始考卷或複習，也能在心情不好或周遭干擾時維持學習品質。', 0.950),
('child_C', 'perseverance', 'counseling_record', '即使討厭英文、感到疲累或面對較難的理化與生物概念，仍會補做單字庫、完成複習，並主動求助直到理解。', 0.950),
('child_C', 'social_intelligence', 'counseling_record', '會主動與老師和同儕聊天、分享興趣，也能察覺他人情緒與團體氣氛，並在適當時候調整自己的互動方式。', 0.950),
('child_C', 'zest', 'counseling_record', '對道具、動漫、遊戲與活動展現高度投入，分享感興趣的內容時精神明顯提升，也能把活動轉化成學習動力。', 0.950),
('child_C', 'honesty', 'counseling_record', '能坦然說出自己分心、後悔承擔任務、對某些概念不熟或需要協助，願意誠實面對自己的情緒與學習瓶頸。', 0.950),
('child_D', 'hope', 'counseling_record', '對升學有明確目標，期待考上大安高工，並會根據模擬考成績調整目標與讀書方向。', 0.950),
('child_D', 'perseverance', 'counseling_record', '面對課業壓力、模擬考與較多作業時，仍能持續完成任務，甚至利用休息時間加強地理與其他弱項。', 0.950),
('child_D', 'self_regulation', 'counseling_record', '能快速完成作業、安排剩餘時間練習，也能在同儕滑手機或教材缺漏時，維持自己的學習節奏並彈性調整。', 0.950),
('child_D', 'love_of_learning', 'counseling_record', '會主動要求補充英文時態與化學莫耳觀念，並希望進一步理解自己尚未掌握的知識。', 0.950),
('child_D', 'curiosity', 'counseling_record', '能覺察自己在英文與化學概念上的疑惑，主動提出問題、分享理解，並透過討論釐清觀念。', 0.950);

INSERT IGNORE INTO child_outfits (child_id, outfit_id, unlocked_source) VALUES
('child_B', 'starter_scarf', 'seed'),
('child_B', 'perseverance_boots', 'counseling_record'),
('child_B', 'self_regulation_shield', 'counseling_record'),
('child_B', 'social_bridge_badge', 'counseling_record'),
('child_B', 'learning_glasses', 'counseling_record'),
('child_B', 'honesty_badge', 'counseling_record'),
('child_C', 'starter_scarf', 'seed'),
('child_C', 'self_regulation_shield', 'counseling_record'),
('child_C', 'perseverance_boots', 'counseling_record'),
('child_C', 'social_bridge_badge', 'counseling_record'),
('child_C', 'zest_scarf', 'counseling_record'),
('child_C', 'honesty_badge', 'counseling_record'),
('child_D', 'starter_scarf', 'seed'),
('child_D', 'hope_compass', 'counseling_record'),
('child_D', 'perseverance_boots', 'counseling_record'),
('child_D', 'self_regulation_shield', 'counseling_record'),
('child_D', 'learning_glasses', 'counseling_record'),
('child_D', 'curiosity_hat', 'counseling_record');
