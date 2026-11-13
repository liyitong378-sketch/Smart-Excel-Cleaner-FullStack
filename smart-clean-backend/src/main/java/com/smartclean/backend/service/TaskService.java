package com.smartclean.backend.service;

import com.smartclean.backend.entity.CleanTask;
import com.smartclean.backend.mapper.CleanTaskMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.time.LocalDateTime;
import java.util.UUID;

@Service
public class TaskService {

    @Autowired
    private CleanTaskMapper taskMapper;

    // 定义文件存储路径（放在项目根目录的 uploads 文件夹下）
    private final String uploadDir = System.getProperty("user.dir") + "/uploads/";

    public Long createTask(String taskName, MultipartFile file) throws IOException {
        File dir = new File(uploadDir);
        if (!dir.exists()) dir.mkdirs();

        // 1. 先插入数据库获取 taskId (为了拿ID重命名文件)
        CleanTask task = new CleanTask();
        task.setTaskName(taskName);
        task.setStatus("PENDING");
        task.setFileCount(1);
        task.setCreatedAt(LocalDateTime.now());
        task.setUpdatedAt(LocalDateTime.now());
        taskMapper.insert(task);
        Long taskId = task.getId();

        // 2. 按照固定的名字保存文件 (例如: task_5.xlsx)
        String originalFilename = file.getOriginalFilename();
        String ext = originalFilename.substring(originalFilename.lastIndexOf("."));
        String newFileName = "task_" + taskId + ext; // 文件名绝对固定！

        File dest = new File(uploadDir + newFileName);
        file.transferTo(dest);

        return taskId;
    }
}