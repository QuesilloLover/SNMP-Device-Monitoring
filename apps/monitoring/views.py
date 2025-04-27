from django.shortcuts import render, redirect, get_object_or_404
from .models import Device
from .forms import DeviceForm
import asyncio
from pysnmp.hlapi.v3arch.asyncio import *
from django.http import JsonResponse

async def fetch_snmp_data(device):
    """
    Fetch SNMP data from a device using SNMPv2c.
    """

    snmpEngine = SnmpEngine()
    varBinds = [
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysContact", 0)),
    ]

    target = await UdpTransportTarget.create((device.ip_address, device.port))
    errorIndication, errorStatus, errorIndex, varBindTable = await bulk_cmd(
        snmpEngine,
        CommunityData(device.community, mpModel=1),
        target,
        ContextData(),
        0, 10,
        *varBinds,
    )
    snmpEngine.transportDispatcher.closeDispatcher()

    if errorIndication:
        return [("Error", str(errorIndication))]
    elif errorStatus:
        return [("Error", f"{errorStatus.prettyPrint()} at {errorIndex}")]
    else:
        return [(x[0].prettyPrint(), x[1].prettyPrint()) for x in varBindTable]

def device_list(request):
    """
    List all devices in the database.
    """

    devices = Device.objects.all()
    return render(request, 'monitoring/device_list.html', {'devices': devices})

def add_device(request):
    """
    Add a new device to the database.
    """

    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('device_list')
    else:
        form = DeviceForm()
    return render(request, 'monitoring/add_device.html', {'form': form})

def format_uptime(ticks):
    """
    Convert SNMP sysUpTime ticks to a human-readable format.
    """

    seconds = int(ticks) // 100
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{days}d {hours}m {minutes}s"

def device_info(request, pk):
    """
    Fetch and display SNMP data for a specific device.
    """
    
    device = get_object_or_404(Device, pk=pk)
    snmp_data = asyncio.run(fetch_snmp_data(device))
    
    important_info = {}
    cleaned_snmp_data = []

    for oid, value in snmp_data:
        if "sysName" in oid:
            important_info["Name"] = value
        elif "sysContact" in oid:
            important_info["Contact"] = value
        elif "sysUpTime" in oid:
            important_info["Uptime"] = format_uptime(value)
        elif "sysServices" in oid:
            important_info["Services"] = value
        elif "sysLocation" in oid:
            important_info["Location"] = value
        else:
            cleaned_snmp_data.append((oid, value)) 

    return render(request, 'monitoring/device_info.html', {
        'device': device,
        'snmp_data': cleaned_snmp_data,
        'important_info': important_info
    })



