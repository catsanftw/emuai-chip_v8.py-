import random
import tkinter as tk
from tkinter import filedialog, messagebox
import time

# CHIP-8 constants
CHIP8_WIDTH = 64
CHIP8_HEIGHT = 32
KEYMAP = {
    '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
    'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
    'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
    'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
}

class Chip8:
    def __init__(self):
        self.memory = [0] * 4096
        self.v = [0] * 16
        self.i = 0
        self.pc = 0x200
        self.gfx = [0] * (CHIP8_WIDTH * CHIP8_HEIGHT)
        self.delay_timer = 0
        self.sound_timer = 0
        self.stack = []
        self.key = [0] * 16

        # Load CHIP-8 font set
        self.fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80   # F
        ]
        self.load_fontset()

    def load_fontset(self):
        for i, byte in enumerate(self.fontset):
            self.memory[i] = byte

    def load_rom(self, rom_path):
        try:
            with open(rom_path, "rb") as rom:
                rom_data = rom.read()
                for i, byte in enumerate(rom_data):
                    self.memory[0x200 + i] = byte
            print(f"ROM loaded successfully: {rom_path}")
        except FileNotFoundError:
            print(f"Error: ROM file not found: {rom_path}")
        except Exception as e:
            print(f"Error loading ROM: {e}")

    def emulate_cycle(self):
        try:
            opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]
            print(f"Executing opcode: {hex(opcode)} at PC: {hex(self.pc)}")
            self.pc += 2

            if opcode == 0x00E0:
                self.gfx = [0] * (CHIP8_WIDTH * CHIP8_HEIGHT)
            elif opcode == 0x00EE:
                self.pc = self.stack.pop()
            elif (opcode & 0xF000) == 0x1000:
                self.pc = opcode & 0x0FFF
            elif (opcode & 0xF000) == 0x2000:
                self.stack.append(self.pc)
                self.pc = opcode & 0x0FFF
            elif (opcode & 0xF000) == 0x3000:
                x = (opcode & 0x0F00) >> 8
                if self.v[x] == (opcode & 0x00FF):
                    self.pc += 2
            elif (opcode & 0xF000) == 0x4000:
                x = (opcode & 0x0F00) >> 8
                if self.v[x] != (opcode & 0x00FF):
                    self.pc += 2
            elif (opcode & 0xF000) == 0x5000:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.v[x] == self.v[y]:
                    self.pc += 2
            elif (opcode & 0xF000) == 0x6000:
                x = (opcode & 0x0F00) >> 8
                self.v[x] = opcode & 0x00FF
            elif (opcode & 0xF000) == 0x7000:
                x = (opcode & 0x0F00) >> 8
                self.v[x] += opcode & 0x00FF
            elif (opcode & 0xF000) == 0x8000:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if (opcode & 0x000F) == 0x0000:
                    self.v[x] = self.v[y]
                elif (opcode & 0x000F) == 0x0001:
                    self.v[x] |= self.v[y]
                elif (opcode & 0x000F) == 0x0002:
                    self.v[x] &= self.v[y]
                elif (opcode & 0x000F) == 0x0003:
                    self.v[x] ^= self.v[y]
                elif (opcode & 0x000F) == 0x0004:
                    result = self.v[x] + self.v[y]
                    self.v[0xF] = 1 if result > 0xFF else 0
                    self.v[x] = result & 0xFF
                elif (opcode & 0x000F) == 0x0005:
                    self.v[0xF] = 1 if self.v[x] > self.v[y] else 0
                    self.v[x] -= self.v[y]
                elif (opcode & 0x000F) == 0x0006:
                    self.v[0xF] = self.v[x] & 0x1
                    self.v[x] >>= 1
                elif (opcode & 0x000F) == 0x0007:
                    self.v[0xF] = 1 if self.v[y] > self.v[x] else 0
                    self.v[x] = self.v[y] - self.v[x]
                elif (opcode & 0x000F) == 0x000E:
                    self.v[0xF] = (self.v[x] >> 7) & 0x1
                    self.v[x] <<= 1
            elif (opcode & 0xF000) == 0x9000:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                if self.v[x] != self.v[y]:
                    self.pc += 2
            elif (opcode & 0xF000) == 0xA000:
                self.i = opcode & 0x0FFF
            elif (opcode & 0xF000) == 0xB000:
                self.pc = (opcode & 0x0FFF) + self.v[0]
            elif (opcode & 0xF000) == 0xC000:
                x = (opcode & 0x0F00) >> 8
                self.v[x] = (opcode & 0x00FF) & (random.randint(0, 255))
            elif (opcode & 0xF000) == 0xD000:
                x = (opcode & 0x0F00) >> 8
                y = (opcode & 0x00F0) >> 4
                height = opcode & 0x000F
                pixel = 0
                self.v[0xF] = 0
                for row in range(height):
                    pixel = self.memory[self.i + row]
                    for col in range(8):
                        if (pixel & (0x80 >> col)) != 0:
                            if self.gfx[(self.v[x] + col + ((self.v[y] + row) * CHIP8_WIDTH))] == 1:
                                self.v[0xF] = 1
                            self.gfx[self.v[x] + col + ((self.v[y] + row) * CHIP8_WIDTH)] ^= 1
            elif (opcode & 0xF000) == 0xE000:
                x = (opcode & 0x0F00) >> 8
                if (opcode & 0x00FF) == 0x009E:
                    if self.key[self.v[x]] != 0:
                        self.pc += 2
                elif (opcode & 0x00FF) == 0x00A1:
                    if self.key[self.v[x]] == 0:
                        self.pc += 2
            elif (opcode & 0xF000) == 0xF000:
                x = (opcode & 0x0F00) >> 8
                if (opcode & 0x00FF) == 0x0007:
                    self.v[x] = self.delay_timer
                elif (opcode & 0x00FF) == 0x000A:
                    key_pressed = False
                    for i in range(16):
                        if self.key[i] != 0:
                            self.v[x] = i
                            key_pressed = True
                            break
                    if not key_pressed:
                        self.pc -= 2
                elif (opcode & 0x00FF) == 0x0015:
                    self.delay_timer = self.v[x]
                elif (opcode & 0x00FF) == 0x0018:
                    self.sound_timer = self.v[x]
                elif (opcode & 0x00FF) == 0x001E:
                    self.i += self.v[x]
                elif (opcode & 0x00FF) == 0x0029:
                    self.i = self.v[x] * 5
                elif (opcode & 0x00FF) == 0x0033:
                    self.memory[self.i] = self.v[x] // 100
                    self.memory[self.i + 1] = (self.v[x] // 10) % 10
                    self.memory[self.i + 2] = self.v[x] % 10
                elif (opcode & 0x00FF) == 0x0055:
                    for i in range(x + 1):
                        self.memory[self.i + i] = self.v[i]
                    self.i += x + 1
                elif (opcode & 0x00FF) == 0x0065:
                    for i in range(x + 1):
                        self.v[i] = self.memory[self.i + i]
                    self.i += x + 1

        except IndexError:
            print(f"Error: PC out of bounds: {self.pc}")
        except Exception as e:
            print(f"Emulation error: {e}")

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            if self.sound_timer == 1:
                print("BEEP!")
            self.sound_timer -= 1

class EmulatorWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("CHIP-8 Emulator")

        self.canvas = tk.Canvas(root, width=CHIP8_WIDTH * 10, height=CHIP8_HEIGHT * 10, bg="black")
        self.canvas.pack()

        self.chip8 = Chip8()

        self.rom_loaded = False
        self.running = False

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)

    def open_rom(self):
        rom_path = filedialog.askopenfilename(title="Open ROM File", filetypes=[("CHIP-8 ROM files", "*.ch8")])
        if rom_path:
            self.chip8.load_rom(rom_path)
            self.rom_loaded = True
            print(f"ROM loaded: {rom_path}")
            self.start_emulation()

    def start_emulation(self):
        if not self.rom_loaded:
            messagebox.showwarning("No ROM Loaded", "Please load a ROM file to start emulation.")
            return
        self.running = True
        print("Starting emulation...")
        self.run_emulation()

    def run_emulation(self):
        if self.running:
            self.chip8.emulate_cycle()
            self.chip8.update_timers()
            self.render_graphics()
            self.root.after(16, self.run_emulation)

    def render_graphics(self):
        self.canvas.delete("all")
        for y in range(CHIP8_HEIGHT):
            for x in range(CHIP8_WIDTH):
                if self.chip8.gfx[x + y * CHIP8_WIDTH] == 1:
                    self.canvas.create_rectangle(
                        x * 10, y * 10, x * 10 + 10, y * 10 + 10, fill="white", outline="white"
                    )

    def stop_emulation(self):
        self.running = False
        print("Emulation stopped.")

    def on_key_press(self, event):
        if event.keysym in KEYMAP:
            self.chip8.key[KEYMAP[event.keysym]] = 1

    def on_key_release(self, event):
        if event.keysym in KEYMAP:
            self.chip8.key[KEYMAP[event.keysym]] = 0

def main():
    root = tk.Tk()
    emulator = EmulatorWindow(root)

    menubar = tk.Menu(root)
    root.config(menu=menubar)

    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open ROM", command=emulator.open_rom)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=file_menu)

    root.mainloop()

if __name__ == "__main__":
    main()
