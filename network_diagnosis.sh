#!/bin/bash

echo "🔍 EKS Pod Network Connectivity Diagnosis Script"
echo "================================================"
echo "Time: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS") echo -e "${GREEN}✅ $message${NC}" ;;
        "ERROR") echo -e "${RED}❌ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  $message${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ️  $message${NC}" ;;
    esac
}

# Get pod name
POD_NAME=$(kubectl get pods -o jsonpath='{.items[?(@.metadata.name~"browser-use-deployment")].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    print_status "ERROR" "Cannot find browser-use-deployment pod"
    echo "Available pods:"
    kubectl get pods
    exit 1
fi

print_status "INFO" "Found pod: $POD_NAME"
echo ""

echo "🔍 STEP 1: Basic Pod Information"
echo "================================"
kubectl describe pod $POD_NAME | grep -E "(Node:|IP:|Status:|Conditions:)" || print_status "ERROR" "Failed to get pod info"
echo ""

echo "🔍 STEP 2: DNS Resolution Test"
echo "=============================="
print_status "INFO" "Testing DNS resolution for SageMaker domains..."

# Test DNS resolution
kubectl exec $POD_NAME -- nslookup sagemaker.us-east-1.amazonaws.com > /tmp/dns_test.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "DNS resolution for sagemaker.us-east-1.amazonaws.com works"
else
    print_status "ERROR" "DNS resolution failed for sagemaker.us-east-1.amazonaws.com"
    cat /tmp/dns_test.log
fi

kubectl exec $POD_NAME -- nslookup nhk8sx2goysqdri.studio.us-east-1.sagemaker.aws > /tmp/dns_studio.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "DNS resolution for SageMaker Studio domain works"
else
    print_status "ERROR" "DNS resolution failed for SageMaker Studio domain"
    cat /tmp/dns_studio.log
fi
echo ""

echo "🔍 STEP 3: Internet Connectivity Test"
echo "====================================="
print_status "INFO" "Testing basic internet connectivity..."

kubectl exec $POD_NAME -- curl -I --connect-timeout 10 https://www.google.com > /tmp/internet_test.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "Internet connectivity works"
else
    print_status "ERROR" "No internet connectivity"
    cat /tmp/internet_test.log
fi
echo ""

echo "🔍 STEP 4: AWS Services Connectivity Test"
echo "========================================="
print_status "INFO" "Testing connectivity to AWS services..."

# Test SageMaker API
kubectl exec $POD_NAME -- curl -I --connect-timeout 15 https://sagemaker.us-east-1.amazonaws.com > /tmp/sagemaker_api.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "SageMaker API endpoint accessible"
else
    print_status "ERROR" "Cannot access SageMaker API endpoint"
    cat /tmp/sagemaker_api.log
fi

# Test SageMaker Studio domain
kubectl exec $POD_NAME -- curl -I --connect-timeout 15 https://nhk8sx2goysqdri.studio.us-east-1.sagemaker.aws > /tmp/studio_test.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "SageMaker Studio domain accessible"
else
    print_status "ERROR" "Cannot access SageMaker Studio domain"
    cat /tmp/studio_test.log
fi
echo ""

echo "🔍 STEP 5: Network Configuration Analysis"
echo "========================================"
print_status "INFO" "Analyzing network configuration..."

# Get node information
NODE_NAME=$(kubectl get pod $POD_NAME -o jsonpath='{.spec.nodeName}')
print_status "INFO" "Pod is running on node: $NODE_NAME"

# Get node external IP
NODE_IP=$(kubectl get node $NODE_NAME -o jsonpath='{.status.addresses[?(@.type=="ExternalIP")].address}')
if [ -n "$NODE_IP" ]; then
    print_status "INFO" "Node external IP: $NODE_IP"
else
    print_status "WARNING" "Node has no external IP (likely in private subnet)"
fi

# Check if node has internal IP
NODE_INTERNAL_IP=$(kubectl get node $NODE_NAME -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}')
print_status "INFO" "Node internal IP: $NODE_INTERNAL_IP"
echo ""

echo "🔍 STEP 6: Security Groups and Network Policies"
echo "=============================================="
print_status "INFO" "Checking network policies..."

# Check for network policies
NETWORK_POLICIES=$(kubectl get networkpolicies --all-namespaces --no-headers 2>/dev/null | wc -l)
if [ $NETWORK_POLICIES -gt 0 ]; then
    print_status "WARNING" "Found $NETWORK_POLICIES network policies that might restrict traffic"
    kubectl get networkpolicies --all-namespaces
else
    print_status "INFO" "No network policies found"
fi
echo ""

echo "🔍 STEP 7: Pod Network Details"
echo "============================="
print_status "INFO" "Getting pod network details..."

POD_IP=$(kubectl get pod $POD_NAME -o jsonpath='{.status.podIP}')
print_status "INFO" "Pod IP: $POD_IP"

# Check pod's network namespace
kubectl exec $POD_NAME -- ip route show > /tmp/pod_routes.log 2>&1
if [ $? -eq 0 ]; then
    print_status "INFO" "Pod routing table:"
    cat /tmp/pod_routes.log
else
    print_status "ERROR" "Cannot get pod routing information"
fi
echo ""

echo "🔍 STEP 8: Port Connectivity Test"
echo "================================"
print_status "INFO" "Testing specific port connectivity..."

# Test HTTPS port
kubectl exec $POD_NAME -- nc -zv sagemaker.us-east-1.amazonaws.com 443 > /tmp/port_test.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "Port 443 (HTTPS) is accessible to SageMaker"
else
    print_status "ERROR" "Port 443 (HTTPS) is blocked to SageMaker"
    cat /tmp/port_test.log
fi
echo ""

echo "🔍 STEP 9: Shortener Service Test"
echo "================================"
print_status "INFO" "Testing shortener service connectivity..."

kubectl exec $POD_NAME -- curl -I http://127.0.0.1:8799 > /tmp/shortener_test.log 2>&1
if [ $? -eq 0 ]; then
    print_status "SUCCESS" "Shortener service is accessible"
else
    print_status "ERROR" "Shortener service is not accessible"
    cat /tmp/shortener_test.log
fi
echo ""

echo "📋 DIAGNOSIS SUMMARY"
echo "==================="
print_status "INFO" "Diagnosis completed. Check the results above."
print_status "INFO" "If you see connectivity issues, the problem is likely:"
echo "   1. Pod is in private subnet without NAT Gateway"
echo "   2. Security groups blocking outbound HTTPS traffic"
echo "   3. Network policies restricting traffic"
echo "   4. VPC routing configuration issues"
echo ""
print_status "INFO" "Next steps based on findings:"
echo "   - If DNS fails: Check VPC DNS settings"
echo "   - If internet fails: Check NAT Gateway/Internet Gateway"
echo "   - If AWS services fail: Check security groups and VPC endpoints"
echo ""

# Cleanup temp files
rm -f /tmp/dns_test.log /tmp/dns_studio.log /tmp/internet_test.log /tmp/sagemaker_api.log /tmp/studio_test.log /tmp/pod_routes.log /tmp/port_test.log /tmp/shortener_test.log

echo "🔍 Diagnosis script completed at $(date)"
