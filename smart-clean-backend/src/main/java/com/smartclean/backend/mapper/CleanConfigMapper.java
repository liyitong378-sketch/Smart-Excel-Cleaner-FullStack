package com.smartclean.backend.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.smartclean.backend.entity.CleanConfig;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CleanConfigMapper extends BaseMapper<CleanConfig> {
}