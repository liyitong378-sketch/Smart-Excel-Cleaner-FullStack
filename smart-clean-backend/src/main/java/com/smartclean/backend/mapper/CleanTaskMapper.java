package com.smartclean.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartclean.backend.entity.CleanTask;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CleanTaskMapper extends BaseMapper<CleanTask> {
}