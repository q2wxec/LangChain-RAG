//新建、编辑知识库弹窗信息
import { IUrlListItem, IFileListItem } from '@/utils/types';
import urlResquest from '@/services/urlConfig';
import message from 'ant-design-vue/es/message';
import { getStatus } from '@/utils/utils';
export const useKnowledgeModal = defineStore('knowledgeModal', () => {
  //是否展示弹窗
  const modalVisible = ref(false);
  const setModalVisible = (flag: boolean) => {
    modalVisible.value = flag;
  };

  //是否展示弹窗
  const qaModalVisible = ref(false);
  const setQaModalVisible = (flag: boolean) => {
    qaModalVisible.value = flag;
  };

  //是否展示上传url弹窗
  const urlModalVisible = ref(false);
  const setUrlModalVisible = (flag: boolean) => {
    urlModalVisible.value = flag;
  };

  //弹窗标题
  const modalTitle = ref('上传文档');
  const setModalTitle = (title: string) => {
    modalTitle.value = title;
  };

  //弹窗标题
  const qaModalTitle = ref('上传文档转化QA');
  const setQaModalTitle = (title: string) => {
    qaModalTitle.value = title;
  };

  //是否展示上传url弹窗
  const promptModalVisible = ref(false);
  const setPromptModalVisible = (flag: boolean) => {
    promptModalVisible.value = flag;
  };

  //知识库名称
  const knowledgeName = ref('');
  const setKnowledgeName = (name: string) => {
    knowledgeName.value = name;
  };

  //上传文件的列表
  const fileList = ref<Array<IFileListItem>>([]);
  const setFileList = (list: Array<IFileListItem>) => {
    fileList.value = list;
  };

  //上传网址列表
  const urlList = ref<Array<IUrlListItem>>([]);
  const setUrlList = list => {
    urlList.value = list;
  };

  //获取文件列表
  const getFileList = async (kb_id: string) => {
    try {
      const res: any = await urlResquest.fileList({ kb_id });
      if (res.code == 200) {
        res.data.details.forEach((item: any) => {
          item.errorText = getStatus(item);
        });

        setFileList(res.data.details);
      }
    } catch (e) {
      console.log(e);
      message.error(e.msg || '请求失败');
    }
  };

  //重置内容
  const $reset = () => {
    modalVisible.value = false;
    modalTitle.value = '上传文档';
    qaModalTitle.value = '上传文档转化QA';
    knowledgeName.value = '';
    fileList.value = [];
    urlList.value = [];
  };
  return {
    modalVisible,
    qaModalVisible,
    setModalVisible,
    setQaModalVisible,
    urlModalVisible,
    setUrlModalVisible,
    promptModalVisible,
    setPromptModalVisible,
    knowledgeName,
    setKnowledgeName,
    fileList,
    setFileList,
    urlList,
    setUrlList,
    modalTitle,
    qaModalTitle,
    setModalTitle,
    setQaModalTitle,
    $reset,
    getFileList,
  };
});
