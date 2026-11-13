package com.smartclean.backend.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.smartclean.backend.entity.CleanConfig;
import com.smartclean.backend.entity.CleanTask;
import com.smartclean.backend.mapper.CleanConfigMapper;
import com.smartclean.backend.mapper.CleanTaskMapper;
import com.smartclean.backend.service.TaskService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.FileSystemResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    @Autowired
    private CleanTaskMapper taskMapper;
    @Autowired
    private TaskService taskService;
    @Autowired
    private CleanConfigMapper configMapper;
    @Autowired
    private RestTemplate restTemplate;

    @GetMapping("/test")
    public List<CleanTask> testConnection() { return taskMapper.selectList(null); }

    @PostMapping("/upload")
    public String uploadAndCreate(@RequestParam("taskName") String taskName, @RequestParam("file") MultipartFile file) {
        try { return "上传成功！任务ID: " + taskService.createTask(taskName, file); }
        catch (Exception e) { return "上传失败：" + e.getMessage(); }
    }

    @PostMapping("/delete/{id}")
    public String deleteTask(@PathVariable Long id) {
        try { taskMapper.deleteById(id); return "删除成功"; }
        catch (Exception e) { return "删除失败：" + e.getMessage(); }
    }

    @PostMapping("/config/save")
    public String saveConfig(@RequestBody Map<String, Object> request) {
        Long taskId = Long.valueOf(request.get("taskId").toString());
        String configJson = request.get("configJson").toString();
        QueryWrapper<CleanConfig> wrapper = new QueryWrapper<>();
        wrapper.eq("task_id", taskId);
        CleanConfig existConfig = configMapper.selectOne(wrapper);
        if (existConfig != null) {
            existConfig.setConfigJson(configJson); configMapper.updateById(existConfig);
        } else {
            CleanConfig newConfig = new CleanConfig();
            newConfig.setTaskId(taskId); newConfig.setConfigJson(configJson); newConfig.setCreatedAt(LocalDateTime.now());
            configMapper.insert(newConfig);
        }
        return "配置保存成功";
    }

    @GetMapping("/config/{taskId}")
    public String getConfig(@PathVariable Long taskId) {
        QueryWrapper<CleanConfig> wrapper = new QueryWrapper<>();
        wrapper.eq("task_id", taskId);
        CleanConfig existConfig = configMapper.selectOne(wrapper);
        return (existConfig != null && existConfig.getConfigJson() != null) ? existConfig.getConfigJson() : "{}";
    }

    @PostMapping("/preview/{id}")
    public String previewTask(@PathVariable Long id, @RequestBody Map<String, Object> request) {
        try {
            String configJson = request.get("configJson").toString();
            String uploadDir = System.getProperty("user.dir") + "/uploads/";
            File targetFile = new File(uploadDir + "task_" + id + ".xlsx");
            if (!targetFile.exists()) targetFile = new File(uploadDir + "task_" + id + ".xls");
            if (!targetFile.exists()) return "{\"status\": \"error\", \"message\": \"文件不存在，可能被删了\", \"sheets\": []}";

            Map<String, String> reqBody = new HashMap<>();
            reqBody.put("file_path", targetFile.getAbsolutePath());
            reqBody.put("config_json", configJson);

            return restTemplate.postForObject("http://localhost:5000/api/python/preview", reqBody, String.class);
        } catch (Exception e) {
            return "{\"status\": \"error\", \"message\": \"" + e.getMessage().replace("\"", "'") + "\", \"sheets\": []}";
        }
    }

    @PostMapping("/execute/{id}")
    public String executeTask(@PathVariable Long id) {
        try {
            CleanTask task = taskMapper.selectById(id);
            if (task == null) return "任务不存在";
            String uploadDir = System.getProperty("user.dir") + "/uploads/";
            File targetFile = new File(uploadDir + "task_" + id + ".xlsx");
            if (!targetFile.exists()) targetFile = new File(uploadDir + "task_" + id + ".xls");
            if (!targetFile.exists()) return "找不到该任务的物理文件";

            QueryWrapper<CleanConfig> wrapper = new QueryWrapper<>();
            wrapper.eq("task_id", id);
            CleanConfig config = configMapper.selectOne(wrapper);
            String configJson = config != null ? config.getConfigJson() : "{}";

            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("file_path", targetFile.getAbsolutePath());
            requestBody.put("config_json", configJson);

            String response = restTemplate.postForObject("http://localhost:5000/api/python/execute", requestBody, String.class);
            task.setStatus("SUCCESS"); taskMapper.updateById(task);
            return response;
        } catch (Exception e) {
            return "{\"status\": \"error\", \"message\": \"" + e.getMessage() + "\"}";
        }
    }

    @GetMapping("/download/{id}")
    public ResponseEntity<Resource> downloadFile(@PathVariable Long id) {
        try {
            String uploadDir = System.getProperty("user.dir") + "/uploads/";
            File file = new File(uploadDir + "task_" + id + "_cleaned.xlsx");
            if (!file.exists()) return ResponseEntity.notFound().build();
            Resource resource = new FileSystemResource(file);
            return ResponseEntity.ok().header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + file.getName() + "\"").body(resource);
        } catch (Exception e) { return ResponseEntity.internalServerError().build(); }
    }

    @GetMapping("/columns/{id}")
    public String getColumns(@PathVariable Long id) {
        try {
            String uploadDir = System.getProperty("user.dir") + "/uploads/";
            File targetFile = new File(uploadDir + "task_" + id + ".xlsx");
            if (!targetFile.exists()) targetFile = new File(uploadDir + "task_" + id + ".xls");
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("file_path", targetFile.getAbsolutePath());
            return restTemplate.postForObject("http://localhost:5000/api/python/columns", requestBody, String.class);
        } catch (Exception e) { return "{\"columns\": []}"; }
    }
}