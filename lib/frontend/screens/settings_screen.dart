import 'package:flutter/cupertino.dart';

/// Tela de configurações do app
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _autoSaveToGallery = true;
  bool _highQualityExport = true;
  double _viralThreshold = 70.0;
  int _maxClips = 5;

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Configurações'),
        backgroundColor: CupertinoColors.black,
      ),
      child: SafeArea(
        child: ListView(
          children: [
                ],
            ),

            _buildSection(
              'Contas Conectadas',
              [
                 _buildSwitch(
                  'YouTube (Auto-Post)',
                  true, 
                  (v) {},
                ),
                _buildSwitch(
                  'Instagram (Deep Link)',
                  false,
                  (v) {},
                ),
                _buildSwitch(
                  'TikTok (Deep Link)',
                  false,
                  (v) {},
                ),
              ],
            ),
            
            _buildSection(
              'Exportação',
              [
                _buildSwitch(
                  'Salvar automaticamente na galeria',
                  _autoSaveToGallery,
                  (value) => setState(() => _autoSaveToGallery = value),
                ),
                _buildSwitch(
                  'Exportação alta qualidade',
                  _highQualityExport,
                  (value) => setState(() => _highQualityExport = value),
                ),
              ],
            ),
            
            _buildSection(
              'Análise Viral',
              [
                _buildSlider(
                  'Threshold viral',
                  _viralThreshold,
                  50.0,
                  100.0,
                  (value) => setState(() => _viralThreshold = value),
                ),
                _buildStepper(
                  'Máximo de clips',
                  _maxClips,
                  1,
                  10,
                  (value) => setState(() => _maxClips = value),
                ),
              ],
            ),
            
            _buildSection(
              'Sobre',
              [
                _buildInfoRow('Versão', '1.0.0'),
                _buildInfoRow('Build', '1'),
                _buildInfoRow('Modo', '100% Offline'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(String title, List<Widget> children) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 24, 16, 8),
          child: Text(
            title.toUpperCase(),
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: CupertinoColors.systemGrey,
            ),
          ),
        ),
        Container(
          color: CupertinoColors.darkBackgroundGray,
          child: Column(children: children),
        ),
      ],
    );
  }

  Widget _buildSwitch(String title, bool value, ValueChanged<bool> onChanged) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: CupertinoColors.separator,
            width: 0.5,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(fontSize: 16)),
          CupertinoSwitch(value: value, onChanged: onChanged),
        ],
      ),
    );
  }

  Widget _buildSlider(
    String title,
    double value,
    double min,
    double max,
    ValueChanged<double> onChanged,
  ) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: CupertinoColors.separator,
            width: 0.5,
          ),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(title, style: const TextStyle(fontSize: 16)),
              Text(
                '${value.toInt()}',
                style: const TextStyle(
                  fontSize: 16,
                  color: CupertinoColors.systemGrey,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          CupertinoSlider(
            value: value,
            min: min,
            max: max,
            onChanged: onChanged,
          ),
        ],
      ),
    );
  }

  Widget _buildStepper(
    String title,
    int value,
    int min,
    int max,
    ValueChanged<int> onChanged,
  ) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: CupertinoColors.separator,
            width: 0.5,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(title, style: const TextStyle(fontSize: 16)),
          Row(
            children: [
              CupertinoButton(
                padding: EdgeInsets.zero,
                minimumSize: const Size(32, 32),
                onPressed: value > min ? () => onChanged(value - 1) : null,
                child: const Icon(CupertinoIcons.minus_circle),
              ),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Text(
                  '$value',
                  style: const TextStyle(fontSize: 16),
                ),
              ),
              CupertinoButton(
                padding: EdgeInsets.zero,
                minimumSize: const Size(32, 32),
                onPressed: value < max ? () => onChanged(value + 1) : null,
                child: const Icon(CupertinoIcons.plus_circle),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: const BoxDecoration(
        border: Border(
          bottom: BorderSide(
            color: CupertinoColors.separator,
            width: 0.5,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(fontSize: 16)),
          Text(
            value,
            style: const TextStyle(
              fontSize: 16,
              color: CupertinoColors.systemGrey,
            ),
          ),
        ],
      ),
    );
  }
}
