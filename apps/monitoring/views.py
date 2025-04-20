from django.shortcuts import render, redirect, get_object_or_404
from .models import Device
from .forms import DeviceForm
import asyncio
from pysnmp.hlapi.v3arch.asyncio import *

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

def device_info(request, pk):
    """
    Fetch and display SNMP data for a specific device.
    """
    
    device = get_object_or_404(Device, pk=pk)
    snmp_data = asyncio.run(fetch_snmp_data(device))
    return render(request, 'monitoring/device_info.html', {
        'device': device,
        'snmp_data': snmp_data
    })
