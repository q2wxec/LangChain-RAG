<!--
 * @Author: 祝占朋 wb.zhuzp01@rd.netease.com
 * @Date: 2023-11-07 19:32:26
 * @LastEditors: 祝占朋 wb.zhuzhanpeng01@mesg.corp.netease.com
 * @LastEditTime: 2024-01-05 18:50:41
 * @FilePath: /LangChain-RAG-open-source/src/components/UrlUploadDialog.vue
 * @Description: 
-->
<template>
  <Teleport to="body">
    <a-modal
      v-model:open="promptModalVisible"
      :title="modalTitle"
      centered
      width="480px"
      wrap-class-name="upload-file-modal"
      @ok="handleOk"
    >
      <div class="line-url">
        <a-textarea
          v-model:value="promptValue"
          placeholder="textarea with clear icon"
          allow-clear
        />
      </div>
      <template #footer>
        <a-button
          key="submit"
          type="primary"
          class="upload-btn"
          :disabled="!canSubmit"
          :loading="confirmLoading"
          @click="handleOk"
        >
          确定
        </a-button>
      </template>
    </a-modal>
  </Teleport>
</template>
<script lang="ts" setup>
import { useKnowledgeModal } from '@/store/useKnowledgeModal';
import { useKnowledgeBase } from '@/store/useKnowledgeBase';
import urlResquest from '@/services/urlConfig';
import { useOptiionList } from '@/store/useOptiionList';
import { message } from 'ant-design-vue';

const { setKnowledgeName } = useKnowledgeModal();
const { promptModalVisible, modalTitle } = storeToRefs(useKnowledgeModal());
const { currentId, currentKbName } = storeToRefs(useKnowledgeBase());
const { getDetails } = useOptiionList();

const confirmLoading = ref<boolean>(false);

const timer = ref();

const promptValue = ref<string>('');

//控制确认按钮 是否能提交
const canSubmit = computed(() => {
  return promptValue.value.length;
});

watch(
  () => promptModalVisible.value,
  async () => {
    setKnowledgeName(currentKbName.value);
    promptValue.value = '';
    if (promptModalVisible.value) {
      let results = await getPrompt();
      promptValue.value = results;
    }
  }
);

const handleOk = async () => {
  confirmLoading.value = true;
  let results = await senRequest(promptValue.value);
  console.log(results);
  confirmLoading.value = false;
  promptModalVisible.value = false;
  getDetails();
};

const senRequest = async params => {
  try {
    let response = await urlResquest.setPrompt({
      kb_id: currentId.value,
      prompt: params,
    });
    if (+response.code === 200) {
      let data = response?.data;
      return data;
    } else {
      message.error('提交失败');
    }
  } catch (e) {
    message.error(e.msg || '提交失败');
  }
};

const getPrompt = async () => {
  let response = await urlResquest.getPrompt({
    kb_id: currentId.value,
  });
  let data = response?.data;
  return data;
};

onBeforeUnmount(() => {
  if (timer.value) {
    clearTimeout(timer.value);
  }
});
</script>
<style lang="scss" scoped>
.file {
  margin-top: 16px;
  display: flex;
  .box {
    flex: 1;
    height: 248px;
    border-radius: 6px;
    background: #f9f9fc;
    box-sizing: border-box;
    border: 1px dashed #ededed;
  }
}

.line-url {
  margin-top: 16px;
  height: 280px;
  display: flex;
  overflow: auto;

  .mt9 {
    margin-top: 9px;
  }

  :deep(.ant-input) {
    height: 260px;
  }

  :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}

.label {
  display: block;
  width: 82px;
  min-width: 82px;
  text-align: right;
  margin-right: 16px;
  color: $title1;

  .red {
    color: red;
  }
}

.before-upload-box {
  position: relative;
  width: 100%;
  height: 100%;

  &.uploading {
    height: 62px;
    border-bottom: 1px solid #ededed;
  }

  .hide {
    opacity: 0;
  }

  .input {
    position: absolute;
    width: 100%;
    height: 100%;
    z-index: 100;
  }
  .before-upload {
    width: 100%;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
  }
  .upload-text-box {
    display: flex;
    align-items: center;
    justify-content: center;

    svg {
      width: 16px;
      height: 16px;
      margin-right: 4px;
      cursor: pointer;
    }

    .upload-text {
      font-weight: 500;
      font-size: 14px;
      color: $title1;
    }

    .blue {
      color: $baseColor;
      cursor: pointer;
    }
  }

  .desc {
    color: $title3;
    text-align: center;
    margin-top: 8px;
    padding: 0 20px;
  }
}

.upload-box {
  &.upload-list {
    height: 188px;
  }

  .list {
    height: 188px;

    overflow: auto;

    li {
      display: flex;
      align-items: center;
      justify-content: space-around;
      height: 22px;
      margin-bottom: 20px;
      padding: 0 20px 0 16px;

      &:first-child {
        margin-top: 20px;
      }
      svg {
        width: 16px;
        height: 16px;
        margin-right: 4px;
      }

      .name {
        flex: 1;
        width: 0;
        margin-right: 20px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .status-box {
        display: flex;
        width: auto;
        align-items: center;
        justify-content: start;
        margin-right: 5px;

        .loading {
          width: 16px;
          height: 16px;
          margin-right: 4px;
          animation: 2s linear infinite loading;
        }
        .status {
          width: 60px;
          font-size: 14px;
          line-height: 22px;
          height: 22px;
          color: $title1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .delete {
        line-height: 22px;
        color: $title2;
        cursor: pointer;
      }
    }
  }

  .note {
    font-family: PingFang SC;
    font-size: 12px;
    font-weight: normal;
    margin-top: 12px;
    color: $title2;
  }
}

:deep(.ant-input) {
  height: 40px;
}

.upload-btn {
  background: #5147e5 !important;
}
</style>
<style lang="scss">
@keyframes loading {
  0% {
    transform: rotate(0deg);
  }

  50% {
    transform: rotate(180deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
