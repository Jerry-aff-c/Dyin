import React, { useState } from 'react';
import { Button, Form, Input, Modal, Steps, Typography } from 'antd';
import { CheckCircle, ClockCircle, ExclamationCircle, Lock } from '@ant-design/icons';
import { api } from '../services/api';

const { Title, Text } = Typography;
const { Step } = Steps;

interface LicenseActivateProps {
  visible: boolean;
  onSuccess: () => void;
  onCancel: () => void;
  isTrialExpired?: boolean;
}

export const LicenseActivate: React.FC<LicenseActivateProps> = ({
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

  const handleCancel = () => {
    setCurrentStep(0);
    setLicenseInfo(null);
    form.resetFields();
    onCancel();
  };

  return (
    <Modal
      title="授权激活"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={500}
      destroyOnClose
    >
      <Steps current={currentStep} style={{ marginBottom: 32 }}>
        <Step
          title="输入授权码"
          icon={currentStep === 0 ? <ClockCircle /> : currentStep > 0 ? <CheckCircle /> : <Lock />}
        />
        <Step
          title="验证授权"
          icon={currentStep === 1 ? <ClockCircle /> : currentStep > 1 ? <CheckCircle /> : <Lock />}
        />
        <Step
          title="激活成功"
          icon={currentStep === 2 ? <ClockCircle /> : currentStep > 2 ? <CheckCircle /> : <Lock />}
        />
      </Steps>

      {currentStep === 0 && (
        <div className="space-y-4">
          {isTrialExpired && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start">
                <ExclamationCircle className="text-red-500 mr-3 mt-0.5" />
                <div>
                  <Text strong className="text-red-700">试用期已过期</Text>
                  <p className="text-red-600 text-sm mt-1">
                    请输入有效的授权码以继续使用监控功能
                  </p>
                </div>
              </div>
            </div>
          )}

          <Form
            form={form}
            layout="vertical"
            onFinish={handleActivate}
          >
            <Form.Item
              name="licenseKey"
              label="授权码"
              rules={[
                { required: true, message: '请输入授权码' },
                { min: 10, message: '授权码格式不正确' }
              ]}
            >
              <Input.TextArea
                rows={4}
                placeholder="请输入完整的授权码"
                className="font-mono"
              />
            </Form.Item>

            <div className="flex justify-end space-x-3">
              <Button onClick={handleCancel}>
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
              >
                激活
              </Button>
            </div>
          </Form>
        </div>
      )}

      {currentStep === 1 && (
        <div className="flex flex-col items-center py-8">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
          <Title level={4}>正在验证授权码...</Title>
          <Text type="secondary">请稍候，系统正在验证您的授权码</Text>
        </div>
      )}

      {currentStep === 2 && (
        <div className="flex flex-col items-center py-8">
          <div className="bg-green-100 rounded-full p-4 mb-4">
            <CheckCircle className="text-green-500" style={{ fontSize: 32 }} />
          </div>
          <Title level={4}>激活成功！</Title>
          {licenseInfo && (
            <div className="text-center mt-4">
              <Text>授权类型：{licenseInfo.type}</Text>
              <br />
              <Text>到期时间：{new Date(licenseInfo.expiry).toLocaleString()}</Text>
            </div>
          )}
          <Text type="secondary" className="mt-4">
            系统将在3秒后自动关闭此窗口
          </Text>
        </div>
      )}
    </Modal>
  );
};
