package com.smartclean.backend.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("clean_task")
public class CleanTask {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String taskName;
    private String status;
    private Integer fileCount;
    private Integer totalRows;
    private String errorSummary;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}