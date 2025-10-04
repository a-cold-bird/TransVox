echo 开始进行干声分离
echo ===============
python scripts/preset_infer_cli.py  -p "./presets/preset.json" -i "input/" -o "results/" -f wav --extra_output_dir 

echo 分离完成，请查看results文件夹