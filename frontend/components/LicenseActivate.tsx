import React, { useState } from 'react';
import { Modal, Form, Input, Button, Alert, Typography, Steps } from 'antd';
import { KeyOutlined, SafetyCertificateOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { api } from '../services/api';

const { Step } = Steps;
const { Paragraph, Text } = Typography;

interface LicenseActivateProps {
  visible: boolean;
  onSuccess: () => void;
  onCancel: () => void;
  isTrialExpired: boolean;
}

const LicenseActivate: React.FC<LicenseActivateProps> = ({
  visible,
  onSuccess,
  onCancel,
  isTrialExpired
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [licenseInfo, setLicenseInfo] = useState<any>(null);
  
  const handleActivate = async (values: { licenseKey: string }) => {
    setLoading(true);
    try {
      // 调用后端验证接口
      const response = await api.post('/api/monitor/auth/activate', {
        license_key: values.licenseKey
      });
      
      if (response.valid) {
        setLicenseInfo(response);
        setCurrentStep(1);
        // 延迟跳转到步骤2
        setTimeout(() => {
          setCurrentStep(2);
          // 3秒后关闭弹窗
          setTimeout(() => {
            onSuccess();
          }, 3000);
        }, 1500);
      } else {
        throw new Error(response.error || '授权码无效');
      }
    } catch (error: any) {
      Modal.error({
        title: '激活失败',
        content: error.message || '请检查授权码是否正确'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const steps = [
    {
      title: '输入授权码',
      icon: <KeyOutlined />,
      content: (
        <Form form={form} onFinish={handleActivate}>
          {isTrialExpired && (
            <Alert
              type="warning"
              message="试用期已结束"
              description="请输入有效的授权码以继续使用全部功能"
              style={{ marginBottom: 16 }}
              showIcon
            />
          )}
          
          <Form.Item
            name="licenseKey"
            rules={[
              { required: true, message: '请输入授权码' },
              { min: 50, message: '授权码格式不正确' }
            ]}
          >
            <Input.TextArea
              placeholder="请输入授权码（通常由60-80位字符组成）"
              rows={4}
              allowClear
            />
          </Form.Item>
          
          <div style={{ marginTop: 16 }}>
            <Paragraph type="secondary">
              <SafetyCertificateOutlined /> 授权码说明：
            </Paragraph>
            <ul style={{ color: '#666', fontSize: 12 }}>
              <li>月卡：30天使用权，适合短期体验</li>
              <li>半年卡：180天使用权，性价比高</li>
              <li>年卡：365天使用权，最优惠</li>
              <li>授权码与设备绑定，请妥善保管</li>
            </ul>
          </div>
        </Form>
      )
    },
    {
      title: '验证中',
      icon: <SafetyCertificateOutlined />,
      content: (
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <div style={{ marginBottom: 20 }}>
            <SafetyCertificateOutlined style={{ fontSize: 48, color: '#1890ff' }} />
          </div>
          <Paragraph>正在验证授权码，请稍候...</Paragraph>
        </div>
      )
    },
    {
      title: '激活成功',
      icon: <CheckCircleOutlined />,
      content: licenseInfo && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 20 }} />
          <Paragraph strong style={{ fontSize: 16 }}>
            授权激活成功！
          </Paragraph>
          <div style={{ background: '#fafafa', padding: 16, borderRadius: 4, marginTop: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary">授权类型：</Text>
              <Text strong>
                {licenseInfo.type === 'MONTH' ? '月卡' : 
                 licenseInfo.type === 'HALF_YEAR' ? '半年卡' : '年卡'}
              </Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text type="secondary">过期时间：</Text>
              <Text strong>{licenseInfo.expiry}</Text>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text type="secondary">剩余天数：</Text>
              <Text strong type="success">{licenseInfo.remaining_days} 天</Text>
            </div>
          </div>
          <Paragraph type="secondary" style={{ marginTop: 16 }}>
            窗口将在3秒后自动关闭...
          </Paragraph>
        </div>
      )
    }
  ];
  
  return (
    <Modal
      title="授权激活"
      visible={visible}
      onCancel={onCancel}
      footer={
        currentStep === 0 ? (
          <>
            <Button onClick={onCancel}>取消</Button>
            <Button
              type="primary"
              loading={loading}
              onClick={() => form.submit()}
            >
              激活授权
            </Button>
          </>
        ) : null
      }
      width={500}
      closable={currentStep === 0}
      maskClosable={false}
    >
      <Steps current={currentStep} size="small" style={{ marginBottom: 24 }}>
        {steps.map(step => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>
      
      <div style={{ minHeight: 200 }}>
        {steps[currentStep].content}
      </div>
    </Modal>
  );
};

export default LicenseActivate;