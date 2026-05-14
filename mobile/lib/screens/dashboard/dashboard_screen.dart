import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shimmer/shimmer.dart';
import '../../providers/dashboard_provider.dart';
import '../../providers/survey_provider.dart';
import '../../widgets/stat_card.dart';
import '../../widgets/survey_card.dart';
import '../survey/submit_survey_screen.dart';
import '../volunteer/match_screen.dart';
import '../survey/survey_list_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      context.read<DashboardProvider>().fetchStats();
      context.read<SurveyProvider>().fetchUrgentNeeds();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: RefreshIndicator(
        color: const Color(0xFF00BFA5),
        onRefresh: () async {
          await context.read<DashboardProvider>().fetchStats();
          await context.read<SurveyProvider>().fetchUrgentNeeds();
        },
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'INTEL OVERVIEW',
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: const Color(0xFF00BFA5),
                          letterSpacing: 2,
                        ),
                      ),
                      Text(
                        'System Live',
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 24,
                          fontWeight: FontWeight.w900,
                          color: const Color(0xFF0F172A),
                          letterSpacing: -0.5,
                        ),
                      ),
                    ],
                  ),
                  _buildStatusBadge(),
                ],
              ),
              const SizedBox(height: 32),
              
              // Stats Row
              Consumer<DashboardProvider>(
                builder: (context, provider, child) {
                  return Row(
                    children: [
                      StatCard(title: 'Surveys', value: provider.totalSurveys.toString(), color: const Color(0xFF3B82F6), icon: Icons.assignment_rounded),
                      const SizedBox(width: 12),
                      StatCard(title: 'Volunteers', value: provider.activeVolunteers.toString(), color: const Color(0xFF10B981), icon: Icons.people_rounded),
                      const SizedBox(width: 12),
                      StatCard(title: 'Urgent', value: provider.urgentCount.toString(), color: const Color(0xFFF43F5E), icon: Icons.bolt_rounded),
                    ],
                  );
                },
              ),
              const SizedBox(height: 32),
              
              // Intelligence Section
              _buildSectionHeader('Operational Intelligence', subtitle: 'Real-time category distribution'),
              const SizedBox(height: 24),
              _buildCategoryChart(),
              
              const SizedBox(height: 40),
              
              // Urgent Needs Section
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  _buildSectionHeader('Urgent Missions', subtitle: 'Highest priority field needs'),
                  TextButton(
                    onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const SurveyListScreen())),
                    child: Text(
                      'View all',
                      style: GoogleFonts.plusJakartaSans(color: const Color(0xFF00BFA5), fontWeight: FontWeight.w800, fontSize: 12),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildUrgentNeedsList(),
              
              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(color: const Color(0xFF00BFA5).withOpacity(0.1), blurRadius: 10, offset: const Offset(0, 4)),
        ],
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 8,
            height: 8,
            decoration: const BoxDecoration(color: Color(0xFF00BFA5), shape: BoxShape.circle),
          ),
          const SizedBox(width: 8),
          Text(
            'ACTIVE',
            style: GoogleFonts.plusJakartaSans(color: Colors.white, fontSize: 10, fontWeight: FontWeight.w800, letterSpacing: 1),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title, {required String subtitle}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: GoogleFonts.plusJakartaSans(fontSize: 18, fontWeight: FontWeight.w900, color: const Color(0xFF0F172A), letterSpacing: -0.5),
        ),
        Text(
          subtitle,
          style: GoogleFonts.plusJakartaSans(fontSize: 12, color: const Color(0xFF64748B), fontWeight: FontWeight.w600),
        ),
      ],
    );
  }

  Widget _buildCategoryChart() {
    return Container(
      height: 240,
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(32),
        border: Border.all(color: Colors.black.withOpacity(0.03)),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.02), blurRadius: 20, offset: const Offset(0, 10)),
        ],
      ),
      child: Consumer<DashboardProvider>(
        builder: (context, provider, child) {
          final data = provider.categoryBreakdown;
          if (data.isEmpty) return const Center(child: Text('Analyzing data...'));
          
          return BarChart(
            BarChartData(
              alignment: BarChartAlignment.spaceAround,
              maxY: data.values.fold(0, (prev, element) => element > prev ? element : prev).toDouble() + 2,
              barGroups: [
                _buildBarGroup(0, data['healthcare']?.toDouble() ?? 0, const Color(0xFFF43F5E)),
                _buildBarGroup(1, data['food']?.toDouble() ?? 0, const Color(0xFFF59E0B)),
                _buildBarGroup(2, data['education']?.toDouble() ?? 0, const Color(0xFF3B82F6)),
                _buildBarGroup(3, data['sanitation']?.toDouble() ?? 0, const Color(0xFF10B981)),
                _buildBarGroup(4, data['employment']?.toDouble() ?? 0, const Color(0xFFA855F7)),
              ],
              titlesData: FlTitlesData(
                show: true,
                bottomTitles: AxisTitles(
                  sideTitles: SideTitles(
                    showTitles: true,
                    getTitlesWidget: (value, meta) {
                      final style = GoogleFonts.plusJakartaSans(fontSize: 10, fontWeight: FontWeight.w800, color: const Color(0xFF64748B));
                      switch (value.toInt()) {
                        case 0: return Text('H', style: style);
                        case 1: return Text('F', style: style);
                        case 2: return Text('E', style: style);
                        case 3: return Text('S', style: style);
                        case 4: return Text('W', style: style);
                        default: return const Text('');
                      }
                    },
                  ),
                ),
                leftTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
              ),
              borderData: FlBorderData(show: false),
              gridData: const FlGridData(show: false),
            ),
          );
        },
      ),
    );
  }

  BarChartGroupData _buildBarGroup(int x, double y, Color color) {
    return BarChartGroupData(
      x: x,
      barRods: [
        BarChartRodData(
          toY: y,
          gradient: LinearGradient(colors: [color.withOpacity(0.4), color], begin: Alignment.bottomCenter, end: Alignment.topCenter),
          width: 16,
          borderRadius: BorderRadius.circular(8),
          backDrawRodData: BackgroundBarChartRodData(show: true, toY: 10, color: const Color(0xFFF1F5F9)),
        ),
      ],
    );
  }

  Widget _buildUrgentNeedsList() {
    return Consumer<SurveyProvider>(
      builder: (context, provider, child) {
        if (provider.isLoading && provider.urgentNeeds.isEmpty) {
          return Shimmer.fromColors(
            baseColor: Colors.grey[300]!,
            highlightColor: Colors.grey[100]!,
            child: Column(children: List.generate(3, (index) => _buildShimmerItem())),
          );
        }
        if (provider.urgentNeeds.isEmpty) return const Center(child: Text('No urgent needs at this time.'));
        
        return ListView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          itemCount: provider.urgentNeeds.length.clamp(0, 5),
          itemBuilder: (context, index) => SurveyCard(survey: provider.urgentNeeds[index]),
        );
      },
    );
  }

  Widget _buildShimmerItem() {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      height: 120,
      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(24)),
    );
  }
}
