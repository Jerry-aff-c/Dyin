import React, { useState, useEffect, useCallback } from 'react';
import { 
  Table, Card, Row, Col, Statistic, Button, Tag, 
  Image, Input, Select, message, Tooltip, InputNumber 
} from 'antd';
import { 
  PlayCircleOutlined, DownloadOutlined, 
  EyeOutlined, SortAscendingOutlined, 
  SyncOutlined, UserOutlined, VideoCameraOutlined, 
  HeartOutlined, ReloadOutlined 
} from '@ant-design/icons';
import { api } from '../services/api';

const { Search } = Input;
const { Option } = Select;

interface VideoData {
  key: string;
  cover_url: string;
  account_name: string;
  video_desc: string;
  hourly_likes: number;
  total_likes: number;
  follower_count: number;
  video_url: string;
  account_id: string;
  updated_at: string;
}

interface MonitorStatus {
  sec_user_id: string;
  monitoring: boolean;
  last_update: string;
  accounts_count: number;
  user_id: string;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<VideoData[]>([]);
  const [filteredData, setFilteredData] = useState<VideoData[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [sortField, setSortField] = useState<string>('hourly_likes');
  const [sortOrder, setSortOrder] = useState<'ascend' | 'descend'>('descend');
  const [pageSize, setPageSize] = useState<number>(20);
  const [filterAccountName, setFilterAccountName] = useState<string>('');
  const [filterVideoDesc, setFilterVideoDesc] = useState<string>('');
  const [filterMinLikes, setFilterMinLikes] = useState<number | undefined>(undefined);
  const [filterMaxLikes, setFilterMaxLikes] = useState<number | undefined>(undefined);
  const [filterMinHourlyLikes, setFilterMinHourlyLikes] = useState<number | undefined>(undefined);
  const [filterMaxHourlyLikes, setFilterMaxHourlyLikes] = useState<number | undefined>(undefined);
  const [monitorStatus, setMonitorStatus] = useState<MonitorStatus>({
    sec_user_id: '',
    monitoring: false,
    last_update: new Date().toISOString(),
    accounts_count: 0,
    user_id: 'default'
  });
  const [secUserId, setSecUserId] = useState('');
  const [cookie, setCookie] = useState('');
  const [startMonitoringLoading, setStartMonitoringLoading] = useState(false);
  const [monitorProgress, setMonitorProgress] = useState('');
  const [dataLoading, setDataLoading] = useState(false);
  
  // 初始化加载数据
  useEffect(() => {
    fetchMonitorStatus();
    fetchSettings();  // 自动加载设置中的cookie
    fetchMonitoringData();
  }, []);
  
  // 应用筛选
  useEffect(() => {
    applyFilters();
  }, [data, filterAccountName, filterVideoDesc, filterMinLikes, filterMaxLikes, filterMinHourlyLikes, filterMaxHourlyLikes]);
  
  const applyFilters = () => {
    let filtered = [...data];
    
    // 按账号名称筛选（模糊匹配）
    if (filterAccountName) {
      filtered = filtered.filter(item => 
        item.account_name.toLowerCase().includes(filterAccountName.toLowerCase())
      );
    }
    
    // 按视频标题筛选（模糊匹配）
    if (filterVideoDesc) {
      filtered = filtered.filter(item => 
        item.video_desc.toLowerCase().includes(filterVideoDesc.toLowerCase())
      );
    }
    
    // 按总点赞量范围筛选
    if (filterMinLikes !== undefined) {
      filtered = filtered.filter(item => item.total_likes >= filterMinLikes);
    }
    if (filterMaxLikes !== undefined) {
      filtered = filtered.filter(item => item.total_likes <= filterMaxLikes);
    }
    
    // 按近一小时点赞量范围筛选
    if (filterMinHourlyLikes !== undefined) {
      filtered = filtered.filter(item => item.hourly_likes >= filterMinHourlyLikes);
    }
    if (filterMaxHourlyLikes !== undefined) {
      filtered = filtered.filter(item => item.hourly_likes <= filterMaxHourlyLikes);
    }
    
    setFilteredData(filtered);
  };
  
  const fetchMonitorStatus = async () => {
    try {
      const response = await api.get('/api/monitor/status');
      setMonitorStatus(response);
      // 只有当本地secUserId为空时，才从服务器获取的值更新secUserId
      // 这样可以避免覆盖用户正在输入的值
      if (!secUserId) {
        setSecUserId(response.sec_user_id);
      }
    } catch (error) {
      console.error('获取监控状态失败:', error);
    }
  };
  
  const fetchSettings = async () => {
    try {
      const settings = await api.get('/api/settings');
      // 只有当本地cookie为空时，才从服务器获取的值更新cookie
      // 这样可以避免覆盖用户正在输入的值
      if (!cookie) {
        setCookie(settings.cookie || '');
      }
    } catch (error) {
      console.error('获取设置失败:', error);
    }
  };
  
  const fetchMonitoringData = async () => {
    try {
      setDataLoading(true);
      setData([]); // 清空现有数据，显示加载状态
      const response = await api.get('/api/monitor/data');
      const processedData = processTableData(response.data);
      setData(processedData);
      if (processedData.length === 0) {
        message.info('暂无监控数据，请先启动监控任务');
      }
    } catch (error) {
      message.warning('暂无监控数据，请先启动监控任务');
      console.error('获取监控数据失败:', error);
    } finally {
      setDataLoading(false);
    }
  };
  
  const processTableData = (rawData: any[]): VideoData[] => {
    return rawData.map(item => ({
      key: item.video_id,
      cover_url: item.cover_url,
      account_name: item.account_name,
      video_desc: item.video_desc,
      hourly_likes: item.hourly_likes,
      total_likes: item.total_likes,
      follower_count: item.follower_count,
      video_url: item.video_url,
      account_id: item.account_id,
      updated_at: item.updated_at || new Date().toISOString()
    }));
  };
  
  const handleStartMonitoring = async () => {
    if (!secUserId) {
      message.error('请先设置抖音sec_user_id');
      return;
    }
    
    try {
      setStartMonitoringLoading(true);
      setMonitorProgress('正在启动监控任务...');
      
      const response = await api.post('/api/monitor/start', { sec_user_id: secUserId, cookie });
      message.success('监控任务已启动');
      setMonitorProgress('监控任务启动成功，正在采集数据...');
      
      // 启动后立即刷新数据
      setTimeout(() => {
        fetchMonitoringData();
        fetchMonitorStatus();
        setMonitorProgress('');
      }, 3000);
    } catch (error: any) {
      message.error(error.detail || '启动监控失败');
      setMonitorProgress('');
    } finally {
      setStartMonitoringLoading(false);
    }
  };
  
  const handleStopMonitoring = async () => {
    try {
      const response = await api.post('/api/monitor/stop');
      message.success('监控任务已停止');
      // 重新获取状态
      setTimeout(fetchMonitorStatus, 1000);
    } catch (error: any) {
      message.error(error.detail || '停止监控失败');
    }
  };
  
  const handleSetSecUserId = async () => {
    if (!secUserId) {
      message.error('请输入sec_user_id');
      return;
    }
    
    try {
      const response = await api.post('/api/monitor/set-sec-user-id', { sec_user_id: secUserId });
      message.success('sec_user_id设置成功');
      // 更新本地状态，不需要重新获取
      setMonitorStatus(prev => ({
        ...prev,
        sec_user_id: secUserId
      }));
    } catch (error: any) {
      message.error(error.detail || '设置失败');
    }
  };
  
  const handleDownload = async (record: VideoData) => {
    try {
      // 这里可以调用原项目的下载API
      // 暂时使用模拟下载
      message.success(`开始下载视频: ${record.video_desc}`);
      console.log('下载视频:', record.video_url);
    } catch (error) {
      message.error('下载失败');
    }
  };
  
  const handleBatchDownload = () => {
    const selectedVideos = data.filter(item => 
      selectedRowKeys.includes(item.key)
    );
    
    if (selectedVideos.length === 0) {
      message.warning('请先选择视频');
      return;
    }
    
    // 批量下载逻辑
    selectedVideos.forEach(video => handleDownload(video));
    message.success(`已开始下载 ${selectedVideos.length} 个视频`);
  };
  
  const columns = [
    {
      title: '作品封面',
      dataIndex: 'cover_url',
      width: 100,
      render: (url: string, record: VideoData) => (
        <div style={{ position: 'relative' }}>
          <Image
            src={url}
            alt="封面"
            width={80}
            height={60}
            style={{ borderRadius: 4, cursor: 'pointer' }}
            preview={{
              mask: <EyeOutlined />,
              src: url
            }}
          />
          <PlayCircleOutlined 
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: 24,
              color: 'rgba(255, 255, 255, 0.8)',
              cursor: 'pointer'
            }}
            onClick={() => window.open(record.video_url, '_blank')}
          />
        </div>
      )
    },
    {
      title: '账号名称',
      dataIndex: 'account_name',
      width: 120,
      sorter: true,
      render: (text: string, record: VideoData) => (
        <div>
          <div>{text}</div>
          <Tag color="blue" style={{ fontSize: 10 }}>
            粉丝: {(record.follower_count / 10000).toFixed(1)}w
          </Tag>
        </div>
      )
    },
    {
      title: '作品名称',
      dataIndex: 'video_desc',
      width: 200,
      ellipsis: true,
      render: (text: string, record: VideoData) => (
        <a 
          href={record.video_url} 
          target="_blank" 
          rel="noopener noreferrer"
          style={{ color: '#1890ff' }}
        >
          {text || '无标题'}
        </a>
      )
    },
    {
      title: '近一小时点赞',
      dataIndex: 'hourly_likes',
      width: 120,
      sorter: true,
      defaultSortOrder: 'descend' as 'descend',
      render: (value: number) => (
        <div style={{ 
          color: value > 0 ? '#52c41a' : value < 0 ? '#f5222d' : '#999',
          fontWeight: 'bold'
        }}>
          {value > 0 ? `+${value}` : value}
          {value > 1000 && <Tag color="red" style={{ marginLeft: 4 }}>热</Tag>}
        </div>
      )
    },
    {
      title: '总点赞量',
      dataIndex: 'total_likes',
      width: 100,
      sorter: true,
      render: (value: number) => (
        <span style={{ fontWeight: 500 }}>
          {(value / 1000).toFixed(1)}k
        </span>
      )
    },
    {
      title: '操作',
      width: 80,
      render: (_: any, record: VideoData) => (
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          size="small"
          onClick={() => handleDownload(record)}
        >
          下载
        </Button>
      )
    }
  ];
  
  return (
    <div className="dashboard-container" style={{ padding: 24 }}>
      {/* 顶部状态栏 - 重用原项目样式 */}
      <Card className="status-card" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="监控中账号" 
              value={monitorStatus.accounts_count} 
              prefix={<UserOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="今日更新视频" 
              value={data.length} 
              prefix={<VideoCameraOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="近一小时总点赞" 
              value={data.reduce((sum, item) => sum + (item.hourly_likes > 0 ? item.hourly_likes : 0), 0)} 
              prefix={<HeartOutlined />}
            />
          </Col>
          <Col span={6}>
            <Button 
              type="primary" 
              onClick={fetchMonitoringData}
              loading={dataLoading}
              icon={<ReloadOutlined />}
            >
              刷新数据
            </Button>
          </Col>
        </Row>
      </Card>
      
      {/* 监控控制栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                抖音 sec_user_id
              </label>
              <Input
                value={secUserId}
                onChange={(e) => setSecUserId(e.target.value)}
                placeholder="请输入抖音sec_user_id"
                style={{ marginRight: 8 }}
              />
              <Button type="primary" onClick={handleSetSecUserId} style={{ marginTop: 8 }}>
                设置
              </Button>
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                Cookie (可选)
              </label>
              <Input.TextArea
                value={cookie}
                onChange={(e) => setCookie(e.target.value)}
                placeholder="请输入抖音Cookie（可选）"
                rows={2}
              />
            </div>
          </Col>
          <Col span={8}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                监控控制
              </label>
              <div>
                <Button 
                  type="primary" 
                  onClick={handleStartMonitoring}
                  disabled={monitorStatus.monitoring}
                  loading={startMonitoringLoading}
                  style={{ marginRight: 8 }}
                >
                  {monitorStatus.monitoring ? '监控中' : '开始监控'}
                </Button>
                <Button 
                  danger 
                  onClick={handleStopMonitoring}
                  disabled={!monitorStatus.monitoring}
                >
                  停止监控
                </Button>
              </div>
              {monitorProgress && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#1890ff' }}>
                  {monitorProgress}
                </div>
              )}
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                状态: {monitorStatus.monitoring ? 
                  <span style={{ color: '#52c41a' }}>监控中</span> : 
                  <span style={{ color: '#999' }}>未监控</span>
                }
                <br />
                上次更新: {new Date(monitorStatus.last_update).toLocaleString()}
              </div>
            </div>
          </Col>
        </Row>
      </Card>
      
      {/* 筛选器栏 */}
      <Card style={{ marginBottom: 16 }} title="数据筛选">
        <Row gutter={16}>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                账号名称
              </label>
              <Input
                value={filterAccountName}
                onChange={(e) => setFilterAccountName(e.target.value)}
                placeholder="输入账号名称（模糊搜索）"
                allowClear
              />
            </div>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                视频标题
              </label>
              <Input
                value={filterVideoDesc}
                onChange={(e) => setFilterVideoDesc(e.target.value)}
                placeholder="输入视频标题（模糊搜索）"
                allowClear
              />
            </div>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                总点赞量范围
              </label>
              <Input.Group compact>
                <InputNumber
                  style={{ width: '45%' }}
                  placeholder="最小值"
                  value={filterMinLikes}
                  onChange={(value) => setFilterMinLikes(value || undefined)}
                  allowClear
                />
                <InputNumber
                  style={{ width: '45%' }}
                  placeholder="最大值"
                  value={filterMaxLikes}
                  onChange={(value) => setFilterMaxLikes(value || undefined)}
                  allowClear
                />
              </Input.Group>
            </div>
          </Col>
          <Col span={6}>
            <div style={{ marginBottom: 8 }}>
              <label style={{ display: 'block', marginBottom: 4, fontWeight: 500 }}>
                近一小时点赞量范围
              </label>
              <Input.Group compact>
                <InputNumber
                  style={{ width: '45%' }}
                  placeholder="最小值"
                  value={filterMinHourlyLikes}
                  onChange={(value) => setFilterMinHourlyLikes(value || undefined)}
                  allowClear
                />
                <InputNumber
                  style={{ width: '45%' }}
                  placeholder="最大值"
                  value={filterMaxHourlyLikes}
                  onChange={(value) => setFilterMaxHourlyLikes(value || undefined)}
                  allowClear
                />
              </Input.Group>
            </div>
          </Col>
        </Row>
        <Row>
          <Col span={24}>
            <Button onClick={() => {
              setFilterAccountName('');
              setFilterVideoDesc('');
              setFilterMinLikes(undefined);
              setFilterMaxLikes(undefined);
              setFilterMinHourlyLikes(undefined);
              setFilterMaxHourlyLikes(undefined);
            }}>
              清除筛选
            </Button>
          </Col>
        </Row>
      </Card>
      
      {/* 批量操作栏 */}
      {selectedRowKeys.length > 0 && (
        <div style={{ marginBottom: 16, padding: 12, background: '#fafafa', borderRadius: 4 }}>
          已选择 {selectedRowKeys.length} 个视频
          <Button 
            type="primary" 
            icon={<DownloadOutlined />} 
            style={{ marginLeft: 16 }}
            onClick={handleBatchDownload}
          >
            批量下载
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={() => setSelectedRowKeys([])}>
            取消选择
          </Button>
        </div>
      )}
      
      {/* 数据表格 - 重用原项目Table组件 */}
      <Table
        columns={columns}
        dataSource={filteredData}
        rowKey="key"
        loading={dataLoading}
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        pagination={{
          pageSize: pageSize,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50', '100', '200'],
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 条数据`,
          onShowSizeChange: (current, size) => setPageSize(size)
        }}
        onChange={(pagination, filters, sorter) => {
          // 处理排序
          if (sorter.field) {
            setSortField(sorter.field as string);
            setSortOrder(sorter.order as 'ascend' | 'descend');
          }
        }}
        scroll={{ x: 800 }}
      />
    </div>
  );
};

export default Dashboard;