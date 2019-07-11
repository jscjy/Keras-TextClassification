# -*- coding: UTF-8 -*-
# !/usr/bin/python
# @time     :2019/6/8 14:37
# @author   :Mo
# @function :train of CharCNNGraph_kim with baidu-qa-2019 in question title


# 适配linux
import pathlib
import sys
import os
project_path = str(pathlib.Path(os.path.abspath(__file__)).parent.parent.parent)
sys.path.append(project_path)
# 地址
from keras_textclassification.conf.path_config import path_model, path_fineture, path_model_dir, path_hyper_parameters
# 训练验证数据地址
from keras_textclassification.conf.path_config import path_baidu_qa_2019_train, path_baidu_qa_2019_valid
# 数据预处理, 删除文件目录下文件
from keras_textclassification.data_preprocess.text_preprocess import PreprocessText, delete_file
# 模型图
from keras_textclassification.m03_CharCNN.graph_yoon_kim import CharCNNGraph as Graph
# 计算时间
import time


def train(hyper_parameters=None, rate=1.0):
    """
        训练函数
    :param hyper_parameters: json, 超参数
    :param rate: 比率, 抽出rate比率语料取训练
    :return: None
    """
    if not hyper_parameters:
        hyper_parameters = {
        'len_max': 50,  # 句子最大长度, 固定 推荐20-50
        'embed_size': 300,  # 字/词向量维度
        'vocab_size': 20000,  # 这里随便填的，会根据代码里修改
        'trainable': True,  # embedding是静态的还是动态的, 即控制可不可以微调
        'level_type': 'char',  # 级别, 最小单元, 字/词, 填 'char' or 'word'
        'embedding_type': 'random',  # 级别, 嵌入类型, 还可以填'random'、 'bert' or 'word2vec"
        'gpu_memory_fraction': 0.66, #gpu使用率
        'model': {'label': 17,  # 类别数
                  'batch_size': 32,  # 批处理尺寸, 感觉原则上越大越好,尤其是样本不均衡的时候, batch_size设置影响比较大
                  'filters': [2, 3, 4, 5],  # 卷积核尺寸
                  'filters_num': 300,  # 卷积个数 text-cnn:300-600
                  'channel_size': 1,  # CNN通道数
                  'dropout': 0.5,  # 随机失活, 概率
                  'decay_step': 100,  # 学习率衰减step, 每N个step衰减一次
                  'decay_rate': 0.9,  # 学习率衰减系数, 乘法
                  'epochs': 20,  # 训练最大轮次
                  'patience': 3, # 早停,2-3就好
                  'lr': 1e-3,  # 学习率, 对训练会有比较大的影响, 如果准确率一直上不去,可以考虑调这个参数
                  'l2': 1e-9,  # l2正则化
                  'activate_classify': 'softmax',  # 最后一个layer, 即分类激活函数
                  'loss': 'categorical_crossentropy',  # 损失函数
                  'metrics': 'accuracy',  # 保存更好模型的评价标准
                  'is_training': True,  # 训练后者是测试模型
                  'model_path': path_model,
                  # 模型地址, loss降低则保存的依据, save_best_only=True, save_weights_only=True
                  'path_hyper_parameters': path_hyper_parameters,  # 模型(包括embedding)，超参数地址,
                  'path_fineture': path_fineture,  # 保存embedding trainable地址, 例如字向量、词向量、bert向量等
                  # only charCNN_kim
                  'char_cnn_layers': [[50, 1], [100, 2], [150, 3], [200, 4], [200, 5], [200, 6], [200, 7]], # [[25, 1], [50, 2], [75, 3], [100, 4], [125, 5], [150, 6]])  # small
                  'highway_layers': 2, # highway_layers个数
                  'num_rnn_layers': 2, # num_rnn_layers个数
                  'rnn_type': 'LSTM',  # rnn_type类型
                  'rnn_units': 650,    # RNN隐藏层, large is 650, small is 300
                  'len_max_word': 30,  # 最大词语长度,
                  },
        'embedding': {'layer_indexes': [12], # bert取的层数,
                      'corpus_path': '',     # embedding预训练数据地址,不配则会默认取conf里边默认的地址
                        },
        'data':{'train_data': path_baidu_qa_2019_train, # 训练数据
                'val_data': path_baidu_qa_2019_valid    # 验证数据
                },
    }

    # 删除先前存在的模型\embedding微调模型等
    delete_file(path_model_dir)
    time_start = time.time()
    # graph初始化
    graph = Graph(hyper_parameters)
    print("graph init ok!")
    ra_ed = graph.word_embedding
    # 数据预处理
    pt = PreprocessText()
    x_train, y_train = pt.preprocess_label_ques_to_idx(hyper_parameters['embedding_type'],
                                                       hyper_parameters['data']['train_data'],
                                                       ra_ed, rate=rate, shuffle=True)
    x_val, y_val = pt.preprocess_label_ques_to_idx(hyper_parameters['embedding_type'],
                                                   hyper_parameters['data']['val_data'],
                                                   ra_ed, rate=rate, shuffle=True)
    print("data propress ok!")
    print(len(y_train))
    # 训练
    graph.fit(x_train, y_train, x_val, y_val)
    print("耗时:" + str(time.time()-time_start))


if __name__=="__main__":
    train(rate=0.001) # sample条件下设为1,否则训练语料可能会很少
    # 注意: 4G的080Ti的GPU、win10下batch_size=32,len_max=20, gpu<=0.87, 应该就可以bert-fineture了。
    # 全量数据训练一轮(batch_size=32),就能达到80%准确率(验证集), 效果还是不错的
    # win10下出现过错误,gpu、len_max、batch_size配小一点就好:ailed to allocate 3.56G (3822520832 bytes) from device: CUDA_ERROR_OUT_OF_MEMORY: out of memory
    # 参数较多,不适合用bert,会比较慢和OOM

# 1425/1425 [==============================] - 35s 24ms/step - loss: 0.1835 - acc: 0.9986 - val_loss: 2.3703 - val_acc: 0.5000
# Epoch 00014: val_loss improved from 2.44240 to 2.37034, saving model
# Epoch 15/20
