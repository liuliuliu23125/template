# MapProgression

管理玩家长期地图解锁和成功撤离进度。`map_progress_data` 属于 PlayerData，
由 PlayerDataCore 初始化、复制和存档；包外通过 Registry_MapProgression 使用。

地图一默认解锁。地图三在玩家成功从地图二撤离后解锁，事件来源为
`EventType.On_EvacSuccess`，重复撤离不会重复修改或重复解锁。
地图二允许已完成主线任务10或已有地图解锁标记的玩家进入；地图三查询
`IsMapUnlocked`。地图选择 UI 不直接读取玩家数据。

GM 面板的“功能测试 → 地图解锁”提供地图1～4的按钮，通过现有
`cmd -s -Map -Unlock Map_N` 指令在服务端解锁当前玩家并保存进度。
地图四目前仅支持保存解锁标记，尚未接入匹配模式，按钮会明确提示暂未开放。

该包不把地图解锁放入 task_data：任务完成和地图撤离是不同的业务条件。
