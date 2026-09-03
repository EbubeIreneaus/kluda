import { ref, computed } from 'vue'
import { buildReceiptPayload, buildTestPrintPayload, type ReceiptData } from '~/utils/escpos'

// Standard BLE Service UUIDs used by thermal receipt printers
const PRINTER_BLE_SERVICES = [
  '000018f0-0000-1000-8000-00805f9b34fb',
  '49535343-fe7d-4ae5-8fa9-9fafd205e455',
  'e7810a71-73ae-499d-8c15-faa9aef0c3f2',
  '0000ffe0-0000-1000-8000-00805f9b34fb',
  '0000ff00-0000-1000-8000-00805f9b34fb',
  '0000ae00-0000-1000-8000-00805f9b34fb'
]

// Global shared state for printer connection across components
const connectionType = ref<'bluetooth' | 'usb' | 'none'>('none')
const deviceName = ref<string>('')
const isConnecting = ref(false)
const isPrinting = ref(false)
const errorMsg = ref<string>('')

// Device references (not serialized in reactive state)
let bluetoothDevice: any = null
let bluetoothCharacteristic: any = null
let usbDevice: any = null
let usbEndpointNumber = 1

export function usePrinter() {
  const toast = useToast()

  const isBluetoothSupported = computed(() => {
    return typeof navigator !== 'undefined' && 'bluetooth' in navigator
  })

  const isUsbSupported = computed(() => {
    return typeof navigator !== 'undefined' && 'usb' in navigator
  })

  const isConnected = computed(() => {
    return connectionType.value !== 'none'
  })

  const paperWidth = ref<'58mm' | '80mm'>('58mm')
  const autoPrint = ref<boolean>(false)

  // Initialize stored preferences on client
  if (import.meta.client) {
    const storedWidth = localStorage.getItem('kluda_printer_width')
    if (storedWidth === '80mm' || storedWidth === '58mm') {
      paperWidth.value = storedWidth
    }
    autoPrint.value = localStorage.getItem('kluda_printer_autoprint') === 'true'
    const storedName = localStorage.getItem('kluda_printer_name')
    if (storedName && !deviceName.value) {
      deviceName.value = storedName
    }
  }

  function setPaperWidth(width: '58mm' | '80mm') {
    paperWidth.value = width
    if (import.meta.client) {
      localStorage.setItem('kluda_printer_width', width)
    }
  }

  function setAutoPrint(val: boolean) {
    autoPrint.value = val
    if (import.meta.client) {
      localStorage.setItem('kluda_printer_autoprint', String(val))
    }
  }

  /**
   * Connect to Bluetooth Thermal Printer via WebBluetooth
   */
  async function connectBluetooth(): Promise<boolean> {
    if (!isBluetoothSupported.value) {
      errorMsg.value = 'WebBluetooth is not supported on this browser/platform. Use Chrome on Android or a PC.'
      toast.add({
        title: 'Bluetooth Not Supported',
        description: errorMsg.value,
        color: 'error'
      })
      return false
    }

    isConnecting.value = true
    errorMsg.value = ''

    try {
      // Disconnect previous if any
      await disconnect()

      // Request device with printer service UUIDs
      const device = await (navigator as any).bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: PRINTER_BLE_SERVICES
      })

      if (!device) {
        isConnecting.value = false
        return false
      }

      device.addEventListener('gattserverdisconnected', onDeviceDisconnected)

      const server = await device.gatt.connect()

      // Search for writable characteristic among known printer services
      let targetCharacteristic: any = null

      for (const serviceUuid of PRINTER_BLE_SERVICES) {
        try {
          const service = await server.getPrimaryService(serviceUuid)
          const characteristics = await service.getCharacteristics()
          for (const char of characteristics) {
            if (char.properties.write || char.properties.writeWithoutResponse) {
              targetCharacteristic = char
              break
            }
          }
          if (targetCharacteristic) break
        } catch {
          // Continue searching other services
        }
      }

      // If not found in standard services, try getting all primary services
      if (!targetCharacteristic && server.getPrimaryServices) {
        try {
          const services = await server.getPrimaryServices()
          for (const service of services) {
            const characteristics = await service.getCharacteristics()
            for (const char of characteristics) {
              if (char.properties.write || char.properties.writeWithoutResponse) {
                targetCharacteristic = char
                break
              }
            }
            if (targetCharacteristic) break
          }
        } catch {
          // Fall through
        }
      }

      if (!targetCharacteristic) {
        throw new Error('Connected to device, but could not find a writable ESC/POS print channel.')
      }

      bluetoothDevice = device
      bluetoothCharacteristic = targetCharacteristic
      connectionType.value = 'bluetooth'
      deviceName.value = device.name || 'Bluetooth Printer'

      if (import.meta.client) {
        localStorage.setItem('kluda_printer_name', deviceName.value)
      }

      toast.add({
        title: 'Printer Connected',
        description: `Successfully linked with ${deviceName.value}`,
        color: 'success'
      })

      return true
    } catch (err: any) {
      if (err.name === 'NotFoundError') {
        // User cancelled pairing modal
        errorMsg.value = 'Pairing cancelled by user.'
      } else {
        errorMsg.value = err?.message || 'Failed to connect to Bluetooth printer.'
        toast.add({
          title: 'Connection Failed',
          description: errorMsg.value,
          color: 'error'
        })
      }
      return false
    } finally {
      isConnecting.value = false
    }
  }

  /**
   * Connect to USB Thermal Printer via WebUSB
   */
  async function connectUsb(): Promise<boolean> {
    if (!isUsbSupported.value) {
      errorMsg.value = 'WebUSB is not supported on this browser/platform.'
      toast.add({
        title: 'USB Not Supported',
        description: errorMsg.value,
        color: 'error'
      })
      return false
    }

    isConnecting.value = true
    errorMsg.value = ''

    try {
      await disconnect()

      const device = await (navigator as any).usb.requestDevice({
        filters: []
      })

      if (!device) {
        isConnecting.value = false
        return false
      }

      await device.open()
      await device.selectConfiguration(1)

      // Find printer interface (class 7 is printer, or fallback to interface 0)
      let ifaceNumber = 0
      let outEndpoint = 1

      for (const iface of device.configuration.interfaces) {
        for (const alt of iface.alternates) {
          if (alt.interfaceClass === 7 || alt.endpoints.some((e: any) => e.direction === 'out')) {
            ifaceNumber = iface.interfaceNumber
            const ep = alt.endpoints.find((e: any) => e.direction === 'out')
            if (ep) {
              outEndpoint = ep.endpointNumber
            }
            break
          }
        }
      }

      await device.claimInterface(ifaceNumber)

      usbDevice = device
      usbEndpointNumber = outEndpoint
      connectionType.value = 'usb'
      deviceName.value = device.productName || 'USB Thermal Printer'

      if (import.meta.client) {
        localStorage.setItem('kluda_printer_name', deviceName.value)
      }

      toast.add({
        title: 'USB Printer Connected',
        description: `Successfully claimed ${deviceName.value}`,
        color: 'success'
      })

      return true
    } catch (err: any) {
      if (err.name === 'NotFoundError') {
        errorMsg.value = 'USB pairing cancelled.'
      } else {
        errorMsg.value = err?.message || 'Failed to claim USB printer interface.'
        toast.add({
          title: 'USB Connection Failed',
          description: errorMsg.value,
          color: 'error'
        })
      }
      return false
    } finally {
      isConnecting.value = false
    }
  }

  /**
   * Disconnect any active Bluetooth or USB handles
   */
  async function disconnect() {
    try {
      if (bluetoothDevice && bluetoothDevice.gatt && bluetoothDevice.gatt.connected) {
        bluetoothDevice.gatt.disconnect()
      }
      if (usbDevice && usbDevice.opened) {
        await usbDevice.close()
      }
    } catch {
      // Ignore disconnect errors
    } finally {
      bluetoothDevice = null
      bluetoothCharacteristic = null
      usbDevice = null
      connectionType.value = 'none'
    }
  }

  function onDeviceDisconnected() {
    connectionType.value = 'none'
    bluetoothDevice = null
    bluetoothCharacteristic = null
    toast.add({
      title: 'Printer Disconnected',
      description: 'The wireless connection was terminated.',
      color: 'neutral'
    })
  }

  /**
   * Send binary buffer to printer in chunks (respects BLE MTU limits)
   */
  async function sendBuffer(buffer: Uint8Array): Promise<boolean> {
    if (!isConnected.value) {
      throw new Error('No thermal printer is currently connected.')
    }

    isPrinting.value = true

    try {
      if (connectionType.value === 'bluetooth') {
        if (!bluetoothCharacteristic) {
          throw new Error('Bluetooth print channel not ready.')
        }

        // Send in 20-byte chunks with small inter-packet delay to comply with standard BLE ATT MTU limits on mobile devices
        const chunkSize = 20
        for (let offset = 0; offset < buffer.length; offset += chunkSize) {
          const chunk = buffer.slice(offset, offset + chunkSize)
          if (bluetoothCharacteristic.writeValueWithoutResponse) {
            await bluetoothCharacteristic.writeValueWithoutResponse(chunk)
          } else {
            await bluetoothCharacteristic.writeValue(chunk)
          }
          // Small 20ms pause for thermal printer buffer consumption
          await new Promise((r) => setTimeout(r, 20))
        }
      } else if (connectionType.value === 'usb') {
        if (!usbDevice || !usbDevice.opened) {
          throw new Error('USB printer is not open.')
        }
        await usbDevice.transferOut(usbEndpointNumber, buffer)
      }

      return true
    } finally {
      isPrinting.value = false
    }
  }

  /**
   * Print a real checkout receipt from ReceiptData
   */
  async function printReceipt(receipt: ReceiptData): Promise<boolean> {
    try {
      if (!isConnected.value) {
        toast.add({
          title: 'Printer Not Connected',
          description: 'Please connect a Bluetooth or USB thermal printer first.',
          color: 'warning'
        })
        return false
      }

      const payload = buildReceiptPayload(receipt, paperWidth.value)
      await sendBuffer(payload)

      toast.add({
        title: 'Receipt Printed',
        description: `Sent to ${deviceName.value}`,
        color: 'success'
      })
      return true
    } catch (err: any) {
      toast.add({
        title: 'Printing Failed',
        description: err?.message || 'Could not transmit data to thermal printer.',
        color: 'error'
      })
      return false
    }
  }

  /**
   * Print a diagnostic test slip
   */
  async function printTestReceipt(): Promise<boolean> {
    try {
      if (!isConnected.value) {
        toast.add({
          title: 'Printer Not Connected',
          description: 'Connect your printer before running a test print.',
          color: 'warning'
        })
        return false
      }

      const payload = buildTestPrintPayload(paperWidth.value)
      await sendBuffer(payload)

      toast.add({
        title: 'Test Print Dispatched',
        description: 'Check paper output on your thermal printer.',
        color: 'success'
      })
      return true
    } catch (err: any) {
      toast.add({
        title: 'Test Print Failed',
        description: err?.message || 'Transmission error.',
        color: 'error'
      })
      return false
    }
  }

  return {
    isMobile,
    isBluetoothSupported,
    isUsbSupported,
    isConnected,
    connectionType,
    deviceName,
    paperWidth,
    autoPrint,
    isConnecting,
    isPrinting,
    errorMsg,
    setPaperWidth,
    setAutoPrint,
    connectBluetooth,
    connectUsb,
    disconnect,
    printReceipt,
    printTestReceipt
  }
}
