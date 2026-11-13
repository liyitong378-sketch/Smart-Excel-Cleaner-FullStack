package com.smartclean.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("clean_config")
public class CleanConfig {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long taskId;
    private String configJson; // 存储前端的 JSON 字符串
    private LocalDateTime createdAt;
}