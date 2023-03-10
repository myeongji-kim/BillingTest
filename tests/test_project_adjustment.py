import pytest
import libs.InitializeConfig as creditutil
import libs.Metering as metering
import libs.Calculation as calc
import libs.Adjustment as adj
import math


class TestProjectAdjustment:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.cleanData()
        meteringObj = metering.Metering(self.config.month)
        meteringObj.appkey = self.config.appkey[0]
        meteringObj.sendIaaSMetering(counterName="compute.c2.c8m8", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        meteringObj.sendIaaSMetering(counterName="storage.volume.ssd", counterType="DELTA", counterUnit="KB", counterVolume="524288000")
        meteringObj.sendIaaSMetering(counterName="network.floating_ip", counterType="DELTA", counterUnit="HOURS", counterVolume="720")
        meteringObj.sendIaaSMetering(counterName="compute.g2.t4.c8m64", counterType="GAUGE", counterUnit="HOURS", counterVolume="720")

    @pytest.fixture(scope="function", autouse=True)
    def setup(self, env, member, month):
        self.config = creditutil.InitializeConfig(env, member, month)
        self.config.beforeTest()  # to change paymentStatus as REGISTERED

    @pytest.fixture(scope="function", autouse=True)
    def teardown(self, env, member, month):
        yield
        adjObj = adj.Adjustments(self.config.month)
        adjlist = adjObj.inquiryAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0])
        adjObj.deleteAdjustment(adjlist)

    # 프로젝트 고정 할인
    def test_prjAdjTC1(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_DISCOUNT", adjustment=100)
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        expect_result = (statements['charge'] - 100) + math.floor((statements['charge'] - 100) * 0.1)
        self.config.verifyAssert(statements=statements['totalAmount'], payments=total_payments, expected_result=expect_result)

    # 프로젝트 퍼센트 할인
    def test_prjAdjTC2(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="PERCENT_DISCOUNT", adjustment=10)
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        percent_discounted = math.ceil(statements['charge'] * (10 * 0.01))
        expect_result = (statements['charge'] - percent_discounted) + math.floor((statements['charge'] - percent_discounted) * 0.1)
        self.config.verifyAssert(statements=statements['totalAmount'], payments=total_payments, expected_result=expect_result)

    # 프로젝트 고정 할증
    def test_prjAdjTC3(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=10000)
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        expect_result = (statements['charge'] + 10000) + math.floor((statements['charge'] + 10000) * 0.1)
        self.config.verifyAssert(statements=statements['totalAmount'], payments=total_payments, expected_result=expect_result)

    # 프로젝트 고정 할인 + 고정 할증
    def test_prjAdjTC4(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_DISCOUNT", adjustment=100)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=1000)
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        originalCharge = (statements['charge'] + 1000 - 100)
        expect_result = originalCharge + math.floor(originalCharge * 0.1)
        self.config.verifyAssert(statements=statements['totalAmount'], payments=total_payments, expected_result=expect_result)

    # 프로젝트 퍼센트 할인 + 고정 할증
    def test_prjAdjTC5(self):
        adjObj = adj.Adjustments(self.config.month)
        adjObj.projectId = self.config.project_id[0]
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="PERCENT_DISCOUNT", adjustment=10)
        adjObj.applyAdjustment(adjustmentTarget="Project", projectId=self.config.project_id[0],
                               adjustmentType="STATIC_EXTRA", adjustment=2000)
        calcObj = calc.Calculation(self.config.month, self.config.uuid)
        calcObj.recalculationAll()
        # 결제 후 금액 비교
        statements, total_payments = self.config.commonTest()
        originalCharge = (statements['charge'] + 2000) - math.ceil((statements['charge'] + 2000) * 10 * 0.01)
        expect_result = originalCharge + math.floor(originalCharge * 0.1)
        self.config.verifyAssert(statements=statements['totalAmount'], payments=total_payments, expected_result=expect_result)