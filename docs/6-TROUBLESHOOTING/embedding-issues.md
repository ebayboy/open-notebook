# 嵌入问题排查指南

本文档帮助您解决在使用 Open Notebook 时遇到的嵌入（embedding）相关问题。

## 常见问题：源没有文本内容

### 错误信息

```
Source source:XXX has no text to vectorize
```

### 可能原因

1. **源仍在处理中**：当使用异步处理时，源创建后需要等待 `process_source` 命令完成，才能提取文本内容。

2. **文本提取失败**：在内容处理步骤中，文本提取可能失败，导致 `full_text` 保持为空。

3. **源创建时就没有提供文本内容**：某些情况下，源可能被创建但没有有效的文本内容。

### 解决方案

#### 1. 检查源的处理状态

使用以下命令检查源的状态：

```bash
# 检查特定源的状态
curl -X GET "http://localhost:5055/api/sources/{source_id}/status"

# 示例
curl -X GET "http://localhost:5055/api/sources/source:1umo8rals03hicui1azx/status"
```

#### 2. 使用诊断脚本

运行诊断脚本来获取详细信息：

```bash
# 在项目根目录运行
python scripts/diagnose_source.py source:1umo8rals03hicui1azx
```

#### 3. 等待处理完成

如果源状态显示为 `queued` 或 `running`，请等待处理完成后再尝试嵌入。

#### 4. 重试处理

如果源处理失败，可以尝试重新处理：

```bash
# 重试处理源
curl -X POST "http://localhost:5055/api/sources/{source_id}/retry"

# 示例
curl -X POST "http://localhost:5055/api/sources/source:1umo8rals03hicui1azx/retry"
```

#### 5. 检查源内容

确保源包含有效的文本内容：

```bash
# 获取源详情
curl -X GET "http://localhost:5055/api/sources/{source_id}"

# 检查 full_text 字段是否有内容
```

### 预防措施

1. **使用同步处理**：在创建源时设置 `async_processing=false` 以确保处理完成后再返回。

2. **检查处理状态**：在尝试嵌入之前，先检查源的处理状态。

3. **使用重试机制**：如果处理失败，使用重试机制重新处理源。

### 高级诊断

如果需要更深入的诊断，可以查看日志：

```bash
# 查看应用日志
tail -f logs/open-notebook.log

# 查找特定源的处理日志
grep "source:1umo8rals03hicui1azx" logs/open-notebook.log
```

### 联系支持

如果以上方法都无法解决问题，请提供以下信息：

1. 源ID
2. 诊断脚本的输出
3. 相关的日志片段
4. 您尝试的操作步骤
