package com.smartclean.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication
public class SmartCleanBackendApplication {

    public static void main(String[] args) {
        SpringApplication.run(SmartCleanBackendApplication.class, args);
    }

    // 加上这个，让 Spring Boot 管理 RestTemplate，TaskController 里才能注入成功
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}